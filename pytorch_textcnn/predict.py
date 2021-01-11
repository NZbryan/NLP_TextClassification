# coding: UTF-8
import torch
from importlib import import_module
import pickle as pkl

class CnnModel:

    def __init__(self):
        dataset = 'dataset'  # 数据集
        embedding = 'random'
        model_name = 'TextCNN'  # 'TextRCNN'  # TextCNN, TextRNN, FastText, TextRCNN, TextRNN_Att, DPCNN, Transformer
        self.id_to_cate = id_to_cate = {int(x.split(" +++$+++ ")[1]\
            .strip()):x.split(" +++$+++ ")[0] for x in open(dataset \
            + '/data/id_to_cate.txt', encoding='utf-8').readlines()}
        x = import_module(model_name)
        config = x.Config(dataset, embedding)
        self.vocab = pkl.load(open(config.vocab_path, 'rb'))
        config.n_vocab = len(self.vocab)
        self.model = x.Model(config).to(config.device)

        self.model.load_state_dict(torch.load(config.save_path))
        self.model.eval()

    def load_dataset(self,message, pad_size=32):
        UNK, PAD = '<UNK>', '<PAD>'  # 未知字，padding符号
        tokenizer = lambda x: [y for y in x]
        contents = []
        for line in message:
            words_line = []
            token = tokenizer(line)
            seq_len = len(token)
            if pad_size:
                if len(token) < pad_size:
                    token.extend([PAD] * (pad_size - len(token)))
                else:
                    token = token[:pad_size]
                    seq_len = pad_size
            # word to id
            for word in token:
                words_line.append(self.vocab.get(word, self.vocab.get(UNK)))
            contents.append(words_line)
        return torch.LongTensor(contents),"placeholder"

    def predict(self,message):
        if type(message) == str:
            message = [message]
        content = self.load_dataset(message)
        outputs = self.model(content)
        predict_int = torch.max(outputs.data, 1)[1].cpu().numpy()
        # id to category
        predict_class = [self.id_to_cate[i] for i in predict_int]

        return predict_class
    
if __name__ == '__main__':
    cnn_model = CnnModel()
    test_demo = ['美国Nordic Naturals 儿童草莓味DHA鳕鱼油口服液 119ml',
                 'DERMACEPT C10铂金抗氧套装']
    print(cnn_model.predict(test_demo))
