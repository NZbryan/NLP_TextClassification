# coding: UTF-8
import numpy as np
import torch
from sklearn import metrics
import time
from utils import get_time_dif
from transformers import AdamW, BertConfig,get_linear_schedule_with_warmup, BertTokenizer, AlbertForSequenceClassification





def train(config, model, train_iter, dev_iter, test_iter):
    
    start_time = time.time()
    # Get all of the model's parameters as a list of tuples.
    params = list(model.named_parameters())

    # Note: AdamW is a class from the huggingface library (as opposed to pytorch) 
    # I believe the 'W' stands for 'Weight Decay fix"
    optimizer = AdamW(model.parameters(),
                      lr = 2e-5, # args.learning_rate - default is 5e-5, our notebook had 2e-5
                      eps = 1e-8 # args.adam_epsilon  - default is 1e-8.
                    )
    # Create the learning rate scheduler.
    scheduler = get_linear_schedule_with_warmup(optimizer, 
                                                num_warmup_steps = 0, # Default value in run_glue.py
                                                num_training_steps = len(train_iter) * config.num_epochs)

    total_batch = 0  # 记录进行到多少batch
    dev_best_loss = float('inf')
    last_improve = 0  # 记录上次验证集loss下降的batch数
    flag = False  # 记录是否很久没有效果提升

    for epoch in range(config.num_epochs):
        model.train()
        print('Epoch [{}/{}]'.format(epoch + 1, config.num_epochs))
        for i, (trains, labels) in enumerate(train_iter):

            b_input_ids = trains[0].to(config.device)
            b_input_mask = trains[2].to(config.device)
            b_labels = labels.to(config.device)

            model.zero_grad()   
            outputs = model(b_input_ids, 
                        token_type_ids=None, 
                        attention_mask=b_input_mask, 
                            labels=b_labels)
            loss = outputs.loss
            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            # Update the learning rate.
            scheduler.step()

            if total_batch % 100 == 0:
                # 每多少轮输出在训练集和验证集上的效果
                predic = torch.max(outputs.logits, 1)[1].cpu()
                labels = b_labels.data.cpu()
                train_acc = metrics.accuracy_score(labels, predic)
                dev_acc, dev_loss = evaluate(config, model, dev_iter)
                if dev_loss < dev_best_loss:
                    dev_best_loss = dev_loss
                    #torch.save(model.state_dict(), config.save_path)
                    improve = '*'
                    last_improve = total_batch
                else:
                    improve = ''
                time_dif = get_time_dif(start_time)
                msg = 'Iter: {0:>6},  Train Loss: {1:>5.2},  Train Acc: {2:>6.2%},  Val Loss: {3:>5.2},  Val Acc: {4:>6.2%},  Time: {5} {6}'
                print(msg.format(total_batch, loss.item(), train_acc, dev_loss, dev_acc, time_dif, improve))
                model.train()
            total_batch += 1
            if total_batch - last_improve > config.require_improvement:
                # 验证集loss超过1000batch没下降，结束训练
                print("No optimization for a long time, auto-stopping...")
                flag = True
                break
        if flag:
            break
    # 保存fine tuning model
    model.save_pretrained(config.saved_finetuning_path)
    config.tokenizer.save_pretrained(config.saved_finetuning_path)



def test(config, test_iter):
    # test
    model = AlbertForSequenceClassification.from_pretrained(config.saved_finetuning_path)
    model.to(config.device)
    model.eval()
    start_time = time.time()
    test_acc, test_loss, test_report, test_confusion = evaluate(config, model, test_iter, test=True)
    msg = 'Test Loss: {0:>5.2},  Test Acc: {1:>6.2%}'
    print(msg.format(test_loss, test_acc))
    print("Precision, Recall and F1-Score...")
    print(test_report)
    print("Confusion Matrix...")
    print(test_confusion)
    time_dif = get_time_dif(start_time)
    print("Time usage:", time_dif)



def evaluate(config, model, data_iter, test=False):
    model.eval()
    loss_total = 0
    predict_all = np.array([], dtype=int)
    labels_all = np.array([], dtype=int)
    with torch.no_grad():
        for texts, labels in data_iter:
            
            b_input_ids = texts[0].to(config.device)
            b_input_mask = texts[2].to(config.device)
            b_labels = labels.to(config.device)
            
            outputs = model(b_input_ids, 
                            token_type_ids=None, 
                            attention_mask=b_input_mask, 
                            labels=b_labels)
            loss = outputs.loss
            loss_total += loss.item()
            
            predic = torch.max(outputs.logits, 1)[1].cpu().numpy()
            labels = b_labels.data.cpu()
            labels_all = np.append(labels_all, labels)
            predict_all = np.append(predict_all, predic)

    acc = metrics.accuracy_score(labels_all, predict_all)
    if test:
        report = metrics.classification_report(labels_all, predict_all, target_names=config.class_list, digits=4)
        confusion = metrics.confusion_matrix(labels_all, predict_all)
        return acc, loss_total / len(data_iter), report, confusion
    return acc, loss_total / len(data_iter)
    