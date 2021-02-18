# coding: UTF-8
import numpy as np
import torch
from transformers import ElectraTokenizer, ElectraForSequenceClassification


        
class electraModel:

    def __init__(self):
        dataset = 'dataset'  # 数据集
        bert_path = dataset + '/saved_finetuning'
        num_classes = 26
        
        self.set_batch_size = 128
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.id_to_cate = id_to_cate = {int(x.split(" +++$+++ ")[1]\
            .strip()):x.split(" +++$+++ ")[0] for x in open(dataset \
            + '/data/id_to_cate.txt', encoding='utf-8').readlines()}

        self.tokenizer = ElectraTokenizer.from_pretrained(bert_path)
        self.model = ElectraForSequenceClassification.from_pretrained(
            bert_path, # Use the 12-layer BERT model, with an uncased vocab.
            num_labels = num_classes, # The number of output labels--2 for binary classification.#
            output_attentions = False)
        self.model.to(self.device)
        self.model.eval()
    
    def batch_iter(self, data, batch_size=3):
        """生成批次数据"""
        data_len = len(data[0])
        num_batch = int((data_len - 1) / batch_size) + 1

        #indices = np.random.permutation(np.arange(data_len))
        indices = np.arange(data_len)


        input_ids = data[0]
        attention_masks = data[2]

        input_ids_shuffle = input_ids[indices]
        attention_masks_shuffle = attention_masks[indices]

        for i in range(num_batch):
            start_id = i * batch_size
            end_id = min((i + 1) * batch_size, data_len)
            yield input_ids_shuffle[start_id:end_id], attention_masks_shuffle[start_id:end_id]
        
    def load_dataset(self,message, pad_size=32):
        PAD, CLS = '[PAD]', '[CLS]'  # padding符号, bert中综合信息符号
        contents = []
        masks = []
        for line in message:
            token = self.tokenizer.tokenize(line)
            token = [CLS] + token
            seq_len = len(token)
            mask = []
            token_ids = self.tokenizer.convert_tokens_to_ids(token)

            if pad_size:
                if len(token) < pad_size:
                    mask = [1] * len(token_ids) + [0] * (pad_size - len(token))
                    token_ids += ([0] * (pad_size - len(token)))
                else:
                    mask = [1] * pad_size
                    token_ids = token_ids[:pad_size]
                    seq_len = pad_size
            contents.append(token_ids)
            masks.append(mask)
        return torch.LongTensor(contents),"seq_len",torch.LongTensor(masks)

    
    def predict(self,message):
        if type(message) == str:
            message = [message]
        content = self.load_dataset(message)
        
        inputs = {'input_ids':content[0].to(self.device),
                  'attention_mask': content[2].to(self.device)
                 }
        with torch.no_grad():
            outputs = self.model(**inputs)
            result = outputs.logits
            result_int = torch.max(outputs.logits, 1)[1].cpu().numpy()
#             id to category
            predict_class = [self.id_to_cate[i] for i in result_int]
            sm = torch.nn.Softmax(dim=1) 
            probabilities = [round(i,3) for i in torch.max(sm(result),1)[0].detach().numpy().tolist()]
        return {"text":message,"predict_class":predict_class,"probabilities": probabilities}
    
if __name__ == '__main__':
    electra_model = electraModel()
    test_demo = message = ['美国Nordic Naturals 儿童草莓味DHA鳕鱼油口服液 119ml',
             'DERMACEPT C10铂金抗氧套装','美国Nordic Naturals 儿童草莓味DHA鳕鱼油口服液 119ml','美国Nordic Naturals 儿童草莓味DHA鳕鱼油口服液 119ml']
    print(electra_model.predict(test_demo))
