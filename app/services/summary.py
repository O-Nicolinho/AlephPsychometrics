import os
import anthropic
import copy

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

ANIMALS = ["macaw", "snow_leopard", "red_fox", "lion", "crocodile", "moose", "capybara", "quokka", "stoat", "dolphin", "beaver", "wolf", "koala" ]



def generate_summary(big_five: dict, jungian: dict) -> str:

    prompt = (f'I will give you a set of Big 5 and Jungian Cognitive Function scores, both ranging between 0 and 100. '
              f'You will use the scores to give the user an analysis of their personality. You must not explicitly mention the jungian functions scores or OCEAN scores of the user.'
              f' You are however expected to base your analysis primarily on their scores. Try to be insightful. '
              f'Try to give a good overview of the personality of the user. Be warm but honest, NEVER use em dashes or bullet points, just provide a clear paragraph. Try to keep it under 150 words or so.Jump straight into describing the user, start with "You are... or You display or similar. \nHere are the scores:'
              f'openness:{big_five["o"]}, conscientiousness:{big_five["c"]}, extraversion:{big_five["e"]}, agreeableness: {big_five["a"]}, neuroticism:{big_five["n"]}'
              f'\nJung: ni:{jungian["ni"]*100}, ne:{jungian["ne"]*100}, si:{jungian["si"]*100}, se:{jungian["se"]*100}, ti:{jungian["ti"]*100}, te:{jungian["te"]*100}, fi:{jungian["fi"]*100}, fe:{jungian["fe"]*100} ')

    message = client.messages.create(
            model="claude-haiku-5-5",
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}]
        )

    return message.content[0].text


#def pick_animal(big_five: dict, jungian: dict) -> str:
    animal_list = ", ".join(ANIMALS)

    prompt = (
        f'Based on the following personality scores, pick exactly one animal '
        f'from this list that best represents this person: {animal_list}. '
        f'Respond with ONLY the animal name in lowercase, nothing else. '
        f'Big Five — openness: {big_five["o"]}, conscientiousness: {big_five["c"]}, '
        f'extraversion: {big_five["e"]}, agreeableness: {big_five["a"]}, '
        f'neuroticism: {big_five["n"]}. '
        f'Jung — ni:{jungian["ni"]*100}, ne:{jungian["ne"]*100}, '
        f'si:{jungian["si"]*100}, se:{jungian["se"]*100}, '
        f'ti:{jungian["ti"]*100}, te:{jungian["te"]*100}, '
        f'fi:{jungian["fi"]*100}, fe:{jungian["fe"]*100}'
    )

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        messages=[{"role": "user", "content": prompt}]
    )

    animal = message.content[0].text.strip().lower()

    # make sure the model returned a valid animal
    if animal not in ANIMALS:
        animal = "fox"  # safe fallback

    return animal


# our system first finds one of the maxtraits in our list, which currently include:
# openness, agreeableness, conscientiousness, not_agreeableness, not_neuroticism
# and for each of these, it has two to three different animals,
# We always choose between these two to three animals based on extraversion score.
def pick_animal(big_five: dict, jungian: dict) -> str:
    traits = copy.deepcopy(big_five)

    ext = traits["e"]

    # not every max_trait has a corresponding animal,
    #traits["not_o"] = 100 - traits["o"] <- not a valid maxtrait
    #traits["not_c"] = 100 - traits["c"] <- not a valid maxtrait
    #traits["not_e"] = 100 - traits["e"] <- not a valid maxtrait
    traits["not_a"] = 100 - traits["a"]
    traits["not_n"] = 100 - traits["n"]

    traits.pop("e") # not a maxtrait, extraversion is used to pick among a given maxtrait's animals
    traits.pop("n") # not a valid maxtrait

    #

    max = 0
    max_trait = ""
    for k in traits:
        if traits[k] >= max:
            max_trait = k
            max = traits[k]

    match max_trait:
        case "o":
            if ext >= 65:
                return "macaw"
            elif ext <= 35:
                return "snow_leopard"
            else:
                return "red_fox"
        case "c":
            if ext >= 50:
                return "wolf"
            else:
                return "beaver"
        case "a":
            if ext >= 65:
                return "quokka"
            elif ext <= 35:
                return "stoat"
            else:
                return "dolphin"
        case "not_a":
            if ext >= 50:
                return "lion"
            else:
                return "crocodile"
        case "not_n":
            if ext >= 50:
                return "capybara"
            else:
                return "moose"

    return "koala"