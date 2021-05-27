import timeit
import logging
import collections
import re
import torch
from torch.utils.data import DataLoader, RandomSampler, SequentialSampler
from fastprogress.fastprogress import master_bar, progress_bar
from transformers import (
    ElectraTokenizer,
    ElectraForQuestionAnswering,
    squad_convert_examples_to_features
)
from transformers.data.metrics.squad_metrics import (
    compute_predictions_logits,
)
from utils import (to_list, input_to_squad_example, get_answer)
RawResult = collections.namedtuple("RawResult",
                                   ["unique_id", "start_logits", "end_logits"])

logger = logging.getLogger(__name__)

def normalize_answer(s):
    s = re.sub("“", "", s)
    s = re.sub("\"", "", s)
    s = re.sub("”", "", s)
    s = " ".join(re.split(r"\s+", s))
    return s

class FactCorrect:
    def __init__(self,model_path: str):
        self.max_seq_length = 512
        self.doc_stride = 128
        self.do_lower_case = False
        self.max_query_length = 64
        self.n_best_size = 20
        self.max_answer_length = 30
        self.model_name_or_path = "monologg/koelectra-small-v3-discriminator"
        self.model, self.tokenizer = self.load_model(model_path)
        self.threads = 4
        self.eval_batch_size = 32
        if torch.cuda.is_available():
            self.device = 'cuda'
        else:
            self.device = 'cpu'
        self.model.to(self.device)
        self.model.eval()

    def load_model(self, model_path: str, do_lower_case=False):
        # config = ElectraConfig.from_pretrained(model_path + "/config.json")
        tokenizer = ElectraTokenizer.from_pretrained(self.model_name_or_path, do_lower_case=do_lower_case)
        model = ElectraForQuestionAnswering.from_pretrained(model_path)
        return model, tokenizer

    def predict(self, passage: str, question: str):
        example = input_to_squad_example(passage, question)
        features, dataset = squad_convert_examples_to_features(
            examples=example,
            tokenizer=self.tokenizer,
            max_seq_length=self.max_seq_length,
            doc_stride=self.doc_stride,
            max_query_length=self.max_query_length,
            is_training= False,
            return_dataset="pt",
            threads=self.threads,
            tqdm_enabled=False,
        )
        eval_sampler = SequentialSampler(dataset)
        eval_dataloader = DataLoader(dataset, sampler=eval_sampler, batch_size=self.eval_batch_size)

        logger.info("***** Running evaluation *****")
        logger.info("  Num examples = %d", len(dataset))
        logger.info("  Batch size = %d", self.eval_batch_size)

        all_results = []
        start_time = timeit.default_timer()

        for batch in progress_bar(eval_dataloader):
            self.model.eval()
            batch = tuple(t.to(self.device) for t in batch)

            with torch.no_grad():
                inputs = {
                    "input_ids": batch[0],
                    "attention_mask": batch[1],
                    "token_type_ids": batch[2],
                }

                # if args.model_type in ["xlm", "roberta", "distilbert", "distilkobert", "xlm-roberta"]:
                #     del inputs["token_type_ids"]

                example_indices = batch[3]

                outputs = self.model(**inputs)

            for i, example_index in enumerate(example_indices):
                eval_feature = features[example_index.item()]
                unique_id = int(eval_feature.unique_id)
                result = RawResult(unique_id=unique_id,
                                   start_logits=to_list(outputs[0][i]),
                                   end_logits=to_list(outputs[1][i]))

                all_results.append(result)

        evalTime = timeit.default_timer() - start_time
        logger.info("  Evaluation done in total %f secs (%f sec per example)", evalTime, evalTime / len(dataset))
        predictions = compute_predictions_logits(
            example,
            features,
            all_results,
            self.n_best_size,
            self.max_answer_length,
            self.do_lower_case,
            output_prediction_file=None,
            output_nbest_file =None,
            output_null_log_odds_file= None,
            verbose_logging=True,
            version_2_with_negative = False,
            null_score_diff_threshold = 0.0,
            tokenizer= self.tokenizer,
        )
        # results = squad_evaluate(example, predictions)
        # answer = get_answer(example[0], features, all_results, self.n_best_size, self.max_answer_length,
        #                     self.do_lower_case)
        return predictions