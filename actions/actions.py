# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"
import requests
import random
from typing import Any, Text, Dict, List
from rasa_sdk.events import AllSlotsReset
from rasa_sdk.events import SlotSet
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class ResetSlot(Action):

    def name(self):
        return "action_reset_slot"

    def run(self, dispatcher, tracker, domain):
        return [AllSlotsReset()]

class ActionRunSPARQL(Action):
    def name(self) -> Text:
        return "action_run_sparql"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dbpediaOntologyTemplate = "http://dbpedia.org/ontology/{0}"
        sparqlTemplate = """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?oLabel
            WHERE
            {{
            <{subject}> <{predicate}> ?o .
            ?o rdfs:label ?oLabel .
            FILTER(LANG(?oLabel) = \"en\") .
            }}
            """

        intent = tracker.latest_message['intent']['name']
        predicate = dbpediaOntologyTemplate.format(intent)
        
        # linking an entity
        if intent == 'birthPlace':
            entity = tracker.get_slot('person')
        elif intent == 'timeZone':
            entity = tracker.get_slot('location')
        elif intent == 'genre':
            entity = tracker.get_slot('artist')
        else:
            dispatcher.utter_message(text = "Sorry, error :(")

        response = requests.get(url="http://webengineering.ins.hs-anhalt.de:43720/rest/annotate",
                            params={"text": entity, "confidence": 0.5},
                            headers={'accept': 'application/json'},
                            verify=False).json()
        
        if 'Resources' in response:
            for resource in response['Resources']:
                entity_uri = resource["@URI"]
                break # assume we have only one entity
            if not entity_uri:
                dispatcher.utter_message(text = "Sorry, error :(")
        else:
            dispatcher.utter_message(text = "Sorry, error :(")

        # querying the knowledge base
        
        sparql = sparqlTemplate.format(subject=entity_uri, predicate=predicate)

        response = requests.post(url="http://dbpedia.org/sparql",
                            params={'query': sparql},
                            headers={'accept': 'application/sparql-results+json'}).json()

        labels_list = list()
        
        print(sparql)

        for binding in response["results"]["bindings"]:
                if "oLabel" in binding and len(binding["oLabel"]) > 0:
                    labels_list.append(binding["oLabel"]["value"])

        result = random.choice(labels_list)

        # TODO: make it beutiful
        if intent == 'birthPlace':
            return [SlotSet("location", result)]
        elif intent == 'timeZone':
            return [SlotSet("timeZone", result)]
        elif intent == 'genre':
            return [SlotSet("genre", result)]
        else:
            dispatcher.utter_message(text = "Sorry, error :(")
            return []
        
