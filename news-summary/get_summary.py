import torch
import re
import sys, os
import datetime
import pandas as pd
from qa_span_model import FactCorrect
from pororo import Pororo
from kobart_transformers import get_kobart_tokenizer, get_kobart_for_conditional_generation
from transformers import (
    ElectraTokenizer,
)
def normalize_answer(s):
    s = " ".join(re.split(r"\s+", s))
    return s

def abs_summary(model,sentence,tokenizer, device):
    model.to(device)
    model.eval()
    with torch.no_grad():
        test_doc = [tokenizer.encode_plus(sentence, add_special_tokens=True,
                                          max_length=1024,  truncation=True,
                                          padding='max_length')["input_ids"]]

        # tensor, gpu
        test_doc = torch.tensor(test_doc)
        test_doc = test_doc.to(device)

        # Generate Summarizaion
        summary_ids = model.generate(test_doc,
                                     num_beams=5,
                                     no_repeat_ngram_size=2,
                                     temperature=1.0, top_k=-1, top_p=-1,
                                     length_penalty=1.0, min_length=1,
                                     max_length=64
                                     ).to(device)

        # Summarization Preprocessing
        output = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        k = output.split('다.')
        text_summary=""
        if len(k) == 1 :
            text_summary = k[0]+"다."
        else:
            for sent in range(len(k) - 1):
                k[sent] = k[sent] + "다."
                text_summary +=k[sent]

        return text_summary

def qa_span_fact(doc, corrupt):
    # print(corrupt)
    doc = normalize_answer(doc)
    corrupt = normalize_answer(corrupt)

    tok_len = len(tok.tokenize(corrupt))
    if tok_len > 64:
        return

    corrupt = '. '.join(corrupt.split('.'))
    corrupt = " ".join(re.split(r"\s+", corrupt))
    ner_sum = ner(corrupt)
    categories = ("PERSON", "LOCATION", "ORGANIZATION", "CIVILIZATION", "DATE", "TIME", "QUANTITY")
    swap_sum = corrupt
    sp = 0
    for tar, ent in ner_sum:
        if ent != 'O' and ent in categories:
            ep = sp + len(tar)
            # print(len(tar))
            # print("masked ent : {}".format(tar))
            mask_s = swap_sum[:sp] + '[MASK]' + swap_sum[ep:]
            # print("masking : {}".format(mask_s))
            ans = qa_model.predict(doc, mask_s)
            swap_sum = mask_s[:sp] + ans[0] + mask_s[sp + 6:]
            sp += len(ans[0])
            # print("predict : {}".format(ans[0]))
            # print("swaping : {}".format(swap_sum))
            # print()
        else:
            sp += len(tar)

    # print("Abs summary: {}".format(corrupt))
    # print("After QA : {}".format(swap_sum))
    return swap_sum

def main():
    summary = []
    qa_span = []
    id = []
    for i in (range(len(data))):
        df = data.loc[i].contents
        if df:
            sum = abs_summary(model, df, tokenizer, device)
        else:
            sum = ''
        summary.append(sum)
        qa_span.append(qa_span_fact(df, sum))
        id.append(datetime.datetime.now().strftime('%Y%m%d %H ') + str(i))

    data.loc[:,'summary'] = summary
    data.loc[:,'qa_span'] = qa_span
    data.loc[:,'timekey'] = datetime.datetime.now().strftime('%Y%m%d-%H')
    data.loc[:,'id'] = id

    data.to_csv(os.path.join(BASE_DIR, DATA_DIR, FILE_NAME), index = False)

if __name__ == "__main__":
    FILE_TIME = datetime.datetime.now().strftime('%Y%m%d-%H')
    time_objective = f"{FILE_TIME}.csv"

    BASE_DIR = '/workspace/News-Summarization-chatbot/news-summary'
    DATA_DIR = 'crawl_data'

    FILE_NAME = time_objective
    data = pd.read_csv(os.path.join(BASE_DIR, DATA_DIR, FILE_NAME))

    """Abs_summary"""
    model = get_kobart_for_conditional_generation()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.load_state_dict(torch.load("/workspace/News-Summarization-chatbot/news-summary/model/L3.pt", map_location=device))
    tokenizer = get_kobart_tokenizer()

    """Qa_span"""
    model_name_or_path = '/workspace/News-Summarization-chatbot/news-summary/model/QA_span'
    qa_model = FactCorrect(model_name_or_path)
    ner = Pororo(task="ner", lang="ko")
    tok =  ElectraTokenizer.from_pretrained("monologg/koelectra-base-v3-discriminator")
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    main()