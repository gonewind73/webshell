'''
Created on 2017年4月29日

@author: heguofeng
'''
# encoding=utf-8

from algorithm.hmm import HMModel
from segment.extra import seg_stop_words

STATES = {'B', 'M', 'E', 'S'}


def get_tags(src):
    tags = []
    if len(src) == 1:
        tags = ['S']
    elif len(src) == 2:
        tags = ['B', 'E']
    else:
        m_num = len(src) - 2
        tags.append('B')
        tags.extend(['M'] * m_num)
        tags.append('S')
    return tags


def cut_sent(src, tags):
    word_list = []
    start = -1
    started = False

    if len(tags) != len(src):
        return None

    if tags[-1] not in {'S', 'E'}:
        if tags[-2] in {'S', 'E'}:
            tags[-1] = 'S'  # for tags: r".*(S|E)(B|M)"
        else:
            tags[-1] = 'E'  # for tags: r".*(B|M)(B|M)"

    for i in range(len(tags)):
        if tags[i] == 'S':
            if started:
                started = False
                word_list.append(src[start:i])  # for tags: r"BM*S"
            word_list.append(src[i])
        elif tags[i] == 'B':
            if started:
                word_list.append(src[start:i])  # for tags: r"BM*B"
            start = i
            started = True
        elif tags[i] == 'E':
            started = False
            word = src[start:i+1]
            word_list.append(word)
        elif tags[i] == 'M':
            continue
    return word_list


class HMMSegger(HMModel):

    def __init__(self, *args, **kwargs):
        super(HMMSegger, self).__init__(*args, **kwargs)
        self.states = STATES
        self.data = None

    def load_data(self, filename):
        self.data = open(filename, 'r', encoding="utf-8")

    def train(self):
        if not self.inited:
            self.setup()

        # train
        for line in self.data:
            # pre processing
            line = line.strip()
            if not line:
                continue

            # get observes
            observes = []
            for i in range(len(line)):
                if line[i] == " ":
                    continue
                observes.append(line[i])

            # get states
            words = line.split(" ")  # spilt word by whitespace
            states = []
            for word in words:
                if word in seg_stop_words:
                    continue
                states.extend(get_tags(word))

            # resume train
            self.do_train(observes, states)

    def cut(self, sentence):
        try:
            tags = self.do_predict(sentence)
            return cut_sent(sentence, tags)
        except:
            return sentence

    def test(self):
        cases = [
            "我来到北京清华大学",
            "长春市长春节讲话",
            "我们去野生动物园玩",
            "我只是做了一些微小的工作",
        ]
        for case in cases:
            result = self.cut(case)
            for word in result:
                print(word)
            print('')


