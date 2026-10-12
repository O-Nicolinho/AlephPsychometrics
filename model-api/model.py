import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

REPO = "Ritsuk0/aleph-big5-fullp"
tokenizer = AutoTokenizer.from_pretrained(REPO)
model = AutoModelForSequenceClassification.from_pretrained(REPO)

MAX_LEN = 4096
MAX_CHUNKS = 4

model.eval()

def inference(text: str) -> dict:
    """Takes as input a string, preprocesses the string, then passes it as input to the FullP Big 5 model. The function then
    returns a dict with the Big 5 scores that the model predicts for the text (0-100), and also passes a bool which
    communicates whether the input text was truncated or not during chunking."""
    truncated = False

    if text == "":
        raise ValueError("Empty user input")

    #we use the tokenizer on the input text
    enc = tokenizer(text, add_special_tokens=False)

    # the input text represented as a list of tokens
    ids = enc["input_ids"]
    length = len(ids)

    if length == 0:
        raise ValueError("User input leads to 0 tokens")

    #window is how many tokens we can extract from the text per chunk
    # we need to save space for the 2 special tokens
    window = MAX_LEN - tokenizer.num_special_tokens_to_add()

    # the num of complete chunks our text allows for
    chunk_num = length // window
    # the remaining tokens after collecting entire chunks (if possible)
    rem = length % window

    # a list of lists, each entry is a list of tokenids for one chunk
    chunks = []

    idx = 0

    # here we do the actual chunking
    # we divide our token list into sublists with a max num of window tokens
    # then we append each sublist to the chunks array
    for chunk in range(min(chunk_num, MAX_CHUNKS)):
        chunks.append(ids[idx:idx+window])
        idx += window
    # we add the remaining tokens to the list only if we're not passing our 4 chunk limit by doing so
    if rem > 0 and chunk_num < MAX_CHUNKS:
        chunks.append(ids[idx:])

    # checks if we truncated the input string
    if chunk_num > MAX_CHUNKS or (chunk_num == MAX_CHUNKS and rem > 0):
        truncated = True

    chunk_attention_mask = []


    # we transform our python tokenid chunk arrays into torch tensors,
    # and we also create each chunk's corresponding attention mask
    for i in range(len(chunks)):
        chunks[i] = [tokenizer.cls_token_id] + chunks[i] + [tokenizer.sep_token_id]
        chunks[i] = torch.tensor(chunks[i]).unsqueeze(0)
        chunk_attention_mask.append(torch.ones_like(chunks[i]))


    with torch.inference_mode():
        outputs = []

        chunk_x_attentionmask = zip(chunks,chunk_attention_mask)
        for input_ids, attention_mask in chunk_x_attentionmask:
            #we pass in the input tokenids and attention mask for each chunk to the model, and get the output
            result = model(input_ids=input_ids, attention_mask=attention_mask)

            outputs.append(result.logits)
    # a matrix of each chunk's logit scores (chunknum x 5)
    stacked = torch.cat(outputs, dim=0)

    #we get the mean of each chunk's logits for our final score, and we set the scores out of 100
    scores = stacked.clamp(0,1).mean(dim=0) * 100
    scores = scores.tolist() # we get a plain python list of our final scores

    # we init out predictions output dict
    prediction = {}

    # for each big5 trait (in id2label) we add the corresponding score to its entry in our predictions dict
    for i, score in enumerate(scores):
        trait = model.config.id2label[i]
        prediction[trait] = score


    # we add the truncated indicator too
    prediction["truncated"] = truncated
    return prediction