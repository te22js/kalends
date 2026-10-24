"""Modern learning material; never ingested into a world, ledger or NPC mind.

Original paraphrases checked against the named institutional sources on
24 October 2026. No source photographs or reconstructed Latin are included.
"""
import copy

SOURCES = {
    'S2': {'id':'S2','title':'Archaeological Park of Pompeii: Along the streets of Pompeii','url':'https://pompeiisites.org/en/pompeii-map/analysis/along-the-streets-of-pompeii/'},
    'S3': {'id':'S3','title':'Archaeological Park of Pompeii: Nevoleia Tyche','url':'https://pompeiisites.org/en/exhibitions-and-events/nevoleia-tyche-en/'},
    'S4': {'id':'S4','title':'Archaeological Park of Pompeii: Being a woman in ancient Pompeii','url':'https://pompeiisites.org/en/exhibitions/being-a-woman-in-ancient-pompeii/'},
    'S5': {'id':'S5','title':'National Archaeological Museum of Naples: Elections in Pompeii','url':'https://artsandculture.google.com/story/tgUBNHEcEscIJg?hl=en'},
}
for brief_id, source in SOURCES.items():
    source['brief_id'] = brief_id
    source['id'] = {'S2':'LEDGER-S4','S3':'ADDENDUM-S13','S4':'LEDGER-S10','S5':'ADDENDUM-S14'}[brief_id]
CARDS = [
    {'id':'food_counter','title':'A food counter on the street','location':'thermopolium',
     'encounter':'The game represents a counter and inset jar forms. This is a schematic model of the food-counter setting.',
     'claim':'The thermopolium, or food-and-drink counter, of Vetutius Placidus had large storage jars built into its serving counter.',
     'evidence':'The Park describes the surviving counter and its embedded vessels.',
     'limits':'A counter does not establish its exact daily menu or the identity of everyone who worked there.',
     'game_changed':'Sabina, her stock, prices and the flour dispute are fictional. The model is not a surveyed reconstruction.',
     'question':'Which visible feature suggests that customers were served here?',
     'labels':['Historical evidence','Reconstruction','Fictional gameplay'],'source_ids':['S2'],
     'illustration':'The in-game counter is an original schematic reconstruction, not an archaeological photograph.'},
    {'id':'fullery','title':'A home turned into a workplace','location':'fullery',
     'encounter':'The game represents washing basins inside a simplified workshop.',
     'claim':'The Fullonica of Stephanus was a cloth-cleaning workshop adapted from a house. Fullonica means a fullery, where cloth was processed.',
     'evidence':'Washing facilities and changes to the domestic building support its workshop interpretation.',
     'limits':'The conventional building name does not establish every occupant or worker. Precise ownership can be an interpretation.',
     'game_changed':'Chreste, her schedule and the paid shifts offered to Aelia are invented. Chreste is enslaved; Aelia taking a paid shift is a different situation.',
     'question':'What would distinguish a workshop from a room used only for domestic life?',
     'labels':['Historical evidence','Reconstruction','Fictional gameplay'],'source_ids':['S2'],
     'illustration':'The game basins are schematic geometry, not a measured plan.'},
    {'id':'freedwoman','title':'A person who had been freed','location':None,
     'encounter':'Aelia is a fictional freedwoman: she was enslaved and was later freed.',
     'claim':'Naevoleia Tyche’s commemorative monument and inscription identify her as a freedwoman.',
     'evidence':'The Park discusses the inscription on the monument near the Herculaneum Gate. That monument is outside this game district.',
     'limits':'One prominent monument cannot show how every freedwoman lived. Women had varied social statuses and opportunities. The Park’s imagined first-person narration is modern interpretation.',
     'game_changed':'Aelia is not Naevoleia Tyche. Her money, work, access and choices are fictional simplifications, not general Roman legal rights.',
     'question':'Can one prosperous individual stand for everyone who had been freed?',
     'labels':['Historical evidence','Fictional gameplay'],'source_ids':['S3','S4']},
    {'id':'wall_notices','title':'Political messages on walls','location':'street',
     'encounter':'This learning card describes surviving painted notices. It does not identify a game wall as an excavated inscription.',
     'claim':'Pompeian electoral notices could name candidates, the offices sought and supporters.',
     'evidence':'The Naples museum presents painted inscription fragments and explains their recurring forms.',
     'limits':'An endorsement does not establish an election result or equal political rights for every resident.',
     'game_changed':'There is no voting mechanic here. Aelia reading this card implies no eligibility for office. Any decorative wall marks in the model are reconstruction, not quoted ancient text.',
     'question':'What can an endorsement tell you, and what can it leave unknown?',
     'labels':['Historical evidence','Reconstruction'],'source_ids':['S5'],
     'illustration':'Modern English structure guide: candidate → office sought → supporter. This is not a transcription.'},
    {'id':'evidence_and_fiction','title':'Evidence, reconstruction and invented choices','location':None,
     'encounter':'Compare the represented counter or workshop with the delivery dispute you are playing.',
     'claim':'Buildings, objects and inscriptions can support limited historical claims. They do not preserve Sabina’s conversation with Aelia.',
     'evidence':'The linked Park descriptions discuss surviving structures; the museum shows inscribed objects.',
     'limits':'Evidence leaves gaps. A plausible reconstruction remains an interpretation.',
     'game_changed':'Every named game character, exact price, reward, deadline, relationship score and cart agreement is invented for play. The miniature street network is simplified.',
     'question':'Name one externally supported feature and one mechanic created for this experience.',
     'labels':['Historical evidence','Reconstruction','Fictional gameplay'],'source_ids':['S2','S5']},
]


def cards_for(snapshot, commands, read=()):
    world = snapshot.get('world', {})
    # This existing adapter starts every life on the public street. Moving to
    # an interior must not erase that already encountered learning location.
    visited = {'street', world.get('player', {}).get('location')}
    visited.update(c.get('data', {}).get('location') for c in commands if c.get('operation') == 'move' or c.get('operation') == 'action' and c.get('data',{}).get('action') == 'move')
    result = []
    for original in CARDS:
        card = copy.deepcopy(original)
        card['encounter_label'] = 'Reconstruction' if card['id'] in ('food_counter','fullery') else 'Fictional gameplay' if card['id']=='freedwoman' else 'Modern learning material'
        card.update(sources=[copy.deepcopy(SOURCES[s]) for s in card.pop('source_ids')],
                    available=card['location'] is None or card['location'] in visited,
                    read=card['id'] in read, rights='Original prose and schematic game geometry. No external image reproduced.')
        # Stable qualified IDs avoid collision with the older research ledger.
        for source in card['sources']:
            source['qualified_id'] = 'first-session-history-v1:' + source['brief_id']
            source['ledger_crosswalk'] = source['id']
        card['voice'] = 'historian'
        card['primary'] = {'title':card['title'], 'text':card['claim']}
        card['details'] = [
            {'label':'Evidence', 'text':card['evidence'] + ' ' + card['limits']},
            {'label':'Reconstruction', 'text':card.get('illustration', card['encounter'])},
            {'label':'Fictional gameplay', 'text':card['game_changed']},
        ]
        # Geometry must be inspected by the scene before asking someone to
        # identify it visually. The source-backed explanation remains readable.
        card['visual_prompt_requires'] = {'food_counter':'recognizable_counter_and_inset_jars', 'fullery':'recognizable_workshop_basins'}.get(card['id'])
        result.append(card)
    return result
