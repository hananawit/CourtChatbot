
import re
import base64
import webbrowser
from typing import Dict, Text, Any, List, Union, Optional
import datetime
from rasa_sdk import Tracker, Action 
from rasa_sdk.executor import CollectingDispatcher 
from rasa_sdk.forms import FormAction,ActiveLoop
from rasa_sdk.events import AllSlotsReset, SlotSet,EventType,FollowupAction
from rasa_sdk.events import SlotSet, UserUtteranceReverted
from rasa_sdk.events import SlotSet
from datetime import date
from rasa_sdk.types import DomainDict
from pyrsistent import v
from rasa_sdk import Tracker,FormValidationAction
from rasa_sdk.events import SlotSet,AllSlotsReset
import requests
import json
import os

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, logger
from rasa_sdk.events import SlotSet, EventType
from rasa_sdk.events import Restarted
from typing import Text, List, Optional

from rasa_sdk.forms import FormValidationAction

complaintTo=''
compliant=''
complaint_for=''
courtMainServiceId=''
subunitOneId=''
subunitTwoId=''
subunitThreeId=''
referenceNumber=''
isCaseNumberAvailable= ''


class GlobalVariables:
    referenceNumber = None
    isCaseNumberAvailable= None
    data = {"documents": "", "extension": ""}

def connected_to_internet(url='http://10.10.20.211:8080/apis/myfeedback', timeout=20):
    print(url)
    try:
        _ = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        print("No connection available.")
    return False





class ActionResetAllSlots(Action):
    def name(self) -> Text:
        return "action_reset_all_slots"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
   
        return [AllSlotsReset()]


    



class clarificationformAm(FormAction):
    """Example of a custom form action"""

    def name(self) -> Text:
        """Unique identifier of the form"""

        return "clarification_form_am"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill"""
        return ["case_number",]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""
        return {
            "case_number": [
                self.from_text(),
            ],
        }
  
        return [AllSlotsReset()]



class Actioncheck_ref_numberAm(Action):
    def name(self) -> Text:
        return "check_ref_number_am"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        session = requests.Session()

        case_number = tracker.get_slot("case_number")

        hostname = "http://213.55.79.158:8080/api/SearchCase?caseNumber=00/0001/"+case_number
        
        url = hostname
        header = {'Content-type': 'application/json', 'Accept': 'application/json'}
        try:
            if connected_to_internet(url=hostname):
                response_text = session.get(url, headers=header)
                response_json = json.loads(response_text.text)
                GlobalVariables.isCaseNumberAvailable=response_json.get("CaseNumber")
                
                if GlobalVariables.isCaseNumberAvailable is None:
                    message = "በዚህ ማጣቀሻ ቁጥር የተመዘገበ ቅሬታ የለም ሰለዚህ"
                    dispatcher.utter_message(text=message)
                    return [SlotSet("case_number", None),FollowupAction("clarification_form_am")]  # Reset the slot
                else:
                    return [SlotSet("case_number", isCaseNumberAvailable)]  # Set the slot to the correct value
            else:
                message = "ለጊዜው, ይህን ሂደት ማከናወን አልችልም"
                dispatcher.utter_message(text=message)
        except ValueError as e:
            dispatcher.utter_message("no connection available")
        return []




class FetchCourtMainServiceAction(Action):
    def name(self):
        return "action_fetch_court_main_servicce"
    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Define what the form has to do
            after all required slots are filled"""
        

        if GlobalVariables.isCaseNumberAvailable is None:    
            
            return [SlotSet("case_number", None)]
        
        select_option= tracker.latest_message.get("text")
        print("courtMainServiceId",select_option)
        courtMainServiceId= select_option
       
        # hostname = "http://196.189.53.206:8089/complaint/courtServiceMain"
        hostname = "http://localhost:8089/complaint/courtServiceMain"

        print("yegeballlllllllllllllllllllllllllllllllll")
        url = hostname
        late=tracker.latest_message
        

        session = requests.Session()
        message = ""
        header = {'Content-type': 'application/json', 'Accept': '*/*'}

        result = True
        if result:
            try:
                if connected_to_internet(url=hostname):
                    response_text = session.get(url, headers=header)
                    
                    if response_text is None:
                        message = "ለተጠየቀው ምንም መረጃ የለም "
                        dispatcher.utter_message(text=message)
                        return
                    response_json = json.loads(response_text.text)
                    print("hhhhhhh", response_json)
                    childrens=response_json
                    buttons = []
                    print("",childrens)

                    for option in childrens:
                        bname=option['title']
                        bid=option['id']
                        hasSubUnit = "1" if option['hasSubUnit'] else "0"

                        print(bid)
    
                        payload = ("hasSubunit" + hasSubUnit + "inform" + bid)
                        buttons.append({"title": bname, "payload": payload})
                        
                    message = "Please select an option:"
                    dispatcher.utter_message(text=message, buttons=buttons, button_type="vertical")
                    return[]  
                
                else:
                    message = "For the time being, I can not perform this process!"
                    dispatcher.utter_message(text=message)

            except ValueError as e:
                message = "There is information for the requested "
                dispatcher.utter_message(text=message)
                message = " "

            return  []





class ActionSaveCourtServiceMain(Action):

    def name(self) -> Text:
        return "save_court_service_main"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        select_option= tracker.latest_message.get("text") 

        global courtMainServiceId

        a = select_option[:17]  # Extracts the substring from index 0 to index 6 ('request')
        b = select_option[17:]  # Extracts the substring from index 7 to the end ('25f84574-498b-4536-9e26-bfe5ffdf053c')
        print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", select_option[17:]) 
        courtMainServiceId= select_option[17:]

                
        if select_option[10] =="1":
            
            return [SlotSet("courtMainServiceId", select_option[17:]),FollowupAction("action_subunit_one")]
 
        else:
            return [FollowupAction("content_compliant_form")]
         
        




class FetchSubunitOneAction(FormAction):
    def name(self):
        return 'action_subunit_one'
    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Define what the form has to do
            after all required slots are filled"""
   
        select_option = tracker.get_slot("select_option")
        # value = select_option
        print("11111111111111111" ,select_option)


        global subunitOneId

        subunitOneId= select_option[17:]
        global complaintTo
        # hostname =  "http://196.189.53.206:8089/complaint/subUnitOne/courtServiceMain/"+subunitOneId
        hostname =  "http://localhost:8089/complaint/subUnitOne/courtServiceMain/"+subunitOneId

        url = hostname
        print(url)
        
        session = requests.Session()
        message = ""
        header = {'Content-type': 'application/json', 'Accept': '*/*'}

        result = True
        if result:
            try:
                if connected_to_internet(url=hostname):
                    response_text = session.get(url, headers=header)
                    
                    if response_text is None:
                        message = "There is no information for the requested"
                        dispatcher.utter_message(text=message)
                        return
                    response_json = json.loads(response_text.text)
                    childrens=response_json
                    buttons = []
                    print("",childrens)
                    
                    for option in childrens:
                        dname=option['title']
                        bid=option['id']
                        hasSubUnit = "1" if option['hasSubUnit'] else "0"

                        print("this is biddddd",bid)
    
                        payload = ("hasSubunit" + hasSubUnit + "inform" + bid)
                        buttons.append({"title": dname, "payload": payload})
                    message = "Please select an option:"
                    dispatcher.utter_message(text=message, buttons=buttons, button_type="vertical")
             
                    subunitOneId = bid
                    print ("subunitOneId bgggggg", subunitOneId)
    
               
                    # "subunitOneId": subunitOneId
                    # "select_option": select_option
                            
                    return [SlotSet("subunitOneId", subunitOneId)]
                
                     
                else:
                    message = "For time being i can not perform "
                    dispatcher.utter_message(text=message)
           
            except ValueError as e:
                message = "There is information for the requested"
                dispatcher.utter_message(text=message)
                message = " "
            return[]
        




class ActionSubunitOne(Action):

    def name(self) -> Text:
        return "save_subunit_one"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        select_option= tracker.latest_message.get("text")
        subunitOneId=tracker.get_slot("subunitOneId") 
        print("subunitOneId bbbbbbbbbbbbbbbbbbbbbb",subunitOneId)
        
        a = select_option[:17]  # Extracts the substring from index 0 to index 6 ('request')
        b = select_option[17:]  # Extracts the substring from index 7 to the end ('25f84574-498b-4536-9e26-bfe5ffdf053c')
        print ("select_option for one ", select_option)      
                
                
        if select_option[10] =="1":
            return [FollowupAction("action_subunit_two")]
 
        else:
            return [FollowupAction("content_compliant_form")]
         
        
 
class FetchSubunitTwoAction(FormAction):
    def name(self):
        return 'action_subunit_two'
    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Define what the form has to do
            after all required slots are filled"""
   
        select_main = tracker.get_slot("select_option")
        # value = select_option
        print("forrrrrrrrr" ,select_main)


        global subunitTwoId
        subunitTwoId= select_main[17:]
        global complaintTo
        # hostname =  "http://196.189.53.206:8089/complaint/subUnitTwo/subUnitOne/"+subunitTwoId
        hostname =  "http://localhost:8089/complaint/subUnitTwo/subUnitOne/"+subunitTwoId

        url = hostname
        print(url)
        
        session = requests.Session()
        message = ""
        header = {'Content-type': 'application/json', 'Accept': '*/*'}

        result = True
        if result:
            try:
                if connected_to_internet(url=hostname):
                    response_text = session.get(url, headers=header)
                    
                    if response_text is None:
                        message = "There is no information for the requested"
                        dispatcher.utter_message(text=message)
                        return
                    response_json = json.loads(response_text.text)
                    childrens=response_json
                    buttons = []
                    print("",childrens)
                    
                    for option in childrens:
                        dname=option['title']
                        bid=option['id']
                        hasSubUnit = "1" if option['hasSubUnit'] else "0"

                        print(bid)
    
                        payload = ("hasSubunit" + hasSubUnit + "inform" + bid)
                        buttons.append({"title": dname, "payload": payload})
                    message = "አባኮን ዘርፍ ይምረጡ:"
                    dispatcher.utter_message(text=message, buttons=buttons, button_type="vertical")
             
                    
                    subunitTwoId = bid
    
                    # slots_to_set = {
                    # "subunitTwoId": subunitTwoId,
                    # "select_main": select_main,
                    #         }
                    # return [SlotSet("subunitTwoId", subunitTwoId)]
                    return [SlotSet("subunitTwoId", subunitTwoId),SlotSet("subunitTwoId", subunitTwoId)]
              
                else:
                    message = "For time being i can not perform "
                    dispatcher.utter_message(text=message)
           
            except ValueError as e:
                message = "There is information for the requested"
                dispatcher.utter_message(text=message)
                message = " "
            return[]




class ActionSubunitTwo(Action):

    def name(self) -> Text:
        return "save_subunit_two"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        select_main= tracker.latest_message.get("text") 
        
        a = select_main[:17]  # Extracts the substring from index 0 to index 6 ('request')
        b = select_main[17:]  # Extracts the substring from index 7 to the end ('25f84574-498b-4536-9e26-bfe5ffdf053c')
        print("select_option", select_main)    
        print ("select_optionno 3333",select_main)    
                
                
        if select_main[10] =="1":
            return [FollowupAction("action_subunit_three")]
 
        else:
            return [FollowupAction("content_compliant_form")]

 
class FetchSubunitThreeAction(FormAction):
    def name(self):
        return 'action_subunit_three'
    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Define what the form has to do
            after all required slots are filled"""
   
        select_option = tracker.get_slot("select_option")
        # value = select_option
        print("3333333333333333" ,select_option)


        global subunitThreeId
        subunitThreeId= select_option[17:]
        global complaintTo
        # hostname =  "http://196.189.53.206:8089/complaint/subUnitThree/subUnitTwo/"+subunitThreeId
        hostname =  "http://localhost:8089/complaint/subUnitThree/subUnitTwo/"+subunitThreeId

        url = hostname
        print(url)
        
        session = requests.Session()
        message = ""
        header = {'Content-type': 'application/json', 'Accept': '*/*'}

        result = True
        if result:
            try:
                if connected_to_internet(url=hostname):
                    response_text = session.get(url, headers=header)
                    
                    if response_text is None:
                        message = "ለተጠየቀው ምንም መረጃ የለም"
                        dispatcher.utter_message(text=message)
                        return
                    response_json = json.loads(response_text.text)
                    childrens=response_json
                    buttons = []
                    print("",childrens)
                    
                    for option in childrens:
                        dname=option['title']
                        bid=option['id']
                        # hasSubUnit = "1" if option['hasSubUnit'] else "0"

                        print(bid)
    
                        payload = ("inform" + bid)
                        buttons.append({"title": dname, "payload": payload})
                    message = "አባኮን ዘርፍ ይምረጡ:"
                    dispatcher.utter_message(text=message, buttons=buttons, button_type="vertical")
             
                    subunitThreeId = bid

    
                 
                    return [SlotSet("subunitThreeId", subunitThreeId),SlotSet("select_option", select_option)]
                    
                     
                else:
                    message = "ለጊዜው ማከናወን አልችልም "
                    dispatcher.utter_message(text=message)
           
            except ValueError as e:
                message = "ለተጠየቀው ምንም መረጃ የለም"
                dispatcher.utter_message(text=message)
                message = " "
            return[]



class ActionSubunitThree(Action):

    def name(self) -> Text:
        return "save_subunit_three"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        select_option= tracker.latest_message.get("text") 
        
        a = select_option[:17]  # Extracts the substring from index 0 to index 6 ('request')
        b = select_option[17:]  # Extracts the substring from index 7 to the end ('25f84574-498b-4536-9e26-bfe5ffdf053c')
                
            
        return [FollowupAction("content_compliant_form")]


    
class othernew_complaintm(FormAction):
    def name(self) -> Text:
        return "content_compliant_form"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        return ["content","new_slot"]
    def slot_mappings(self) -> Dict[Text, Union[Dict,List[Dict]]]:
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""
        return {

            "content": [
                self.from_text(),
            ],
            
            "new_slot": [
                self.from_text(),
            ]

        }

    def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Process the filled slots and perform necessary actions
        # new_slot = tracker.get_slot("new_slot")
        # if new_slot=="affirm":
        #     return [FollowupAction("form_upload_image")]
 
        # elif new_slot=="affirm":
        #     return [FollowupAction("submit_compliant_en")]


        return []

class Actionchoosenewslot(Action):
    def name(self) -> Text:
        return "action_new_slot"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        new_slot = tracker.latest_message.get("text")
        if new_slot == "accept":
            return [SlotSet("new_slot", new_slot), FollowupAction("form_upload_image")]
        else:
            return [SlotSet("new_slot", new_slot), FollowupAction("submit_compliant_en")]

        return []






class ImageUpload(FormAction):
    def name(self) -> Text:
        return "form_upload_image"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        return ["upload_image"]
    def slot_mappings(self) -> Dict[Text, Union[Dict,List[Dict]]]:
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""
        return {

            "upload_image": [
                self.from_text(),
            ]
            

        }

        return []

class ActionUPLOADPICTURE(Action):
    def name(self) -> Text:
        return "action_upload_image"

    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Define what the form has to do
         after all required slots are filled"""

        session = requests.Session()
        image_id = ""   
        urlimg = "https://api.telegram.org/bot6344667146:AAHNf0PpA8DLx9CdXbItH4TI-ndApEnu3tA"
        r2 = requests.get(urlimg)
        img = base64.b64encode(r2.content)
        

        if tracker.get_slot("upload_image"):
            image_id = tracker.get_slot("upload_image")
            print("image id", image_id)
            url2 = "https://api.telegram.org/bot6344667146:AAHNf0PpA8DLx9CdXbItH4TI-ndApEnu3tA/getFile?file_id=" + image_id
            r = requests.get(url2)
            img = base64.b64encode(r.content)

            resp = json.loads(r.text)
            file_path = resp["result"]["file_path"]

            print("this is " + file_path)
            url3 = "https://api.telegram.org/file/bot6344667146:AAHNf0PpA8DLx9CdXbItH4TI-ndApEnu3tA/" + file_path
            r2 = requests.get(url3)
            img = base64.b64encode(r2.content)
            # Get the file extension from the filename
            file_name = os.path.basename(file_path)
            file_extension = os.path.splitext(file_name)[1]

            # Call the convertToBase64 method to get the Base64 string
            img_base64 = img

            GlobalVariables.data["documents"] = img_base64.decode('utf-8')
            GlobalVariables.data["extension"] = file_extension  # Set the file extension
        
        # print("This  is image iddd",image_id)
        # if image_id!= "":
        #     data["documents"]=img.decode('utf-8')
        #     print("data is .....",data)
               
        
        # try:
            
        #     if connected_to_internet(url=hostname):
                
        #         response_text = session.post(url, json=data)
        #         # response_json = json.loads(response_text.text)
        #         print("respnse jason nw ....   ",response_text)
        #         dispatcher.utter_message("ur document is sent sucessfully")
               
        #     else:
        #          message = "For the time being, I can not perform this process"
        #          dispatcher.utter_message(text=message)


        # except ValueError as e:
        #     message = "no available"
        #     dispatcher.utter_message(text=message)
        return [SlotSet("upload_image", img)]
    



class ActionSubmitcompliant(Action):
    def name(self) -> Text:
        return "submit_compliant_en"

    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Define what the form has to do
         after all required slots are filled"""
        session = requests.Session()
        # hostname = "http://196.189.53.206:8089/complaint/complainat"
        hostname = "http://localhost:8089/complaint/complainat"

        url = hostname
        buttons = []
        
        compliant = tracker.get_slot("compliant")
        if compliant == "ቅ/ጽ/ቤት":
           buttons.append({"title": "sdf", "payload": "‘payload_value’"})
           dispatcher.utter_message(buttons=buttons)
            
            
            # "fileName": tracker.get_slot("upload_image"),

        data={
            "contentForDeputy": tracker.get_slot("content"),
            "caseNumber": tracker.get_slot("case_number"),          
            "fileExtension": GlobalVariables.data["extension"],     
            "courtServiceMain":{
                "id":courtMainServiceId
            },
          
            "subUnitOne":{
                "id":subunitOneId
            },
            "subUnitTwo":{
                "id":subunitTwoId
            },
            "subUnitThree":{
                "id":subunitThreeId
            }, 
            "fileName": GlobalVariables.data["documents"],


        }


        print("data is", data)
        try:
            if connected_to_internet(url=hostname):
                response_text = session.post(url, json=data)
                print("checking")
                response_json = json.loads(response_text.text)
                dispatcher.utter_message("ከእኛ ጋር ስላደረጉት ቆይታ እናመሰግናለን.")
                reference_number = (response_json['referenceNumber'])
                print(reference_number)
                dispatcher.utter_message(" ቅሬታህን ተቀብለናል ,ለሚመለከተው ክፍል እናደርሳለን" +"\n"+ str (reference_number) +"\n"+ "በዚህ ቁጥር የአቤቱታ ሁኔታዎን መከታተል ይችላሉ.")
               
            else:
                message = "አስተያየቶች አልተላኩም። እባክዎ ቆየት ብለው ይሞክሩ"
                dispatcher.utter_message(text=message)
            dispatcher.utter_message(response="action_reset_slots_value")
        except ValueError as e:
            message = "No connection available."
            dispatcher.utter_message(text=message)
            # print("submited")
          
        return [AllSlotsReset(), Restarted()]
    

    
class ReapplycomplinatAm(FormAction):
    """Example of a custom form action"""

    def name(self) -> Text:
        """Unique identifier of the form"""

        return "form_re_apply_compliant_am"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill"""
        return ["reference_number_am","content"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""
        return {
            "reference_number_am": [
                self.from_text(),
            ],
            "content":[
               self.from_text(),
            ],
        }


    def submit(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Define what the form has to do
            after all required slots are filled"""
        referencenumber = tracker.get_slot("reference_number_am")
        content = tracker.get_slot("content")

        session = requests.Session()
        # hostname = "http://196.189.53.206:8089/complaint/complainat/referenceNumber/{referenceNumber}/{responseStatus}/{content}"
        hostname = "http://localhost:8089/complaint/response/referenceNumber/"+referencenumber

        url = hostname
        entryDate = date.today()
        message = ""
        result = True
        if result:
            try:
               if connected_to_internet(url=hostname):
                    response_text = session.post(url)
                    print("checking")
                    response_json = json.loads(response_text.text)
                    dispatcher.utter_message(" ከእኛ ጋር ጊዜዎን እናደንቃለን.")
                    reference_number = (response_json['referenceNumber'])
                    print(reference_number)
                    dispatcher.utter_message(" ቅሬታህን ተቀብለናል። ለሚመለከተው ክፍል እናደርሳለን ." + " " + str(reference_number) + "በዚህ ቁጥር የአቤቱታ ሁኔታዎን መከታተል ይችላሉ።")                

               else:
                message = "ይቅርታ፣ ለጊዜው ይህን ሂደት ማከናወን አልችልም! ስለዚህ ሌሎች ጥያቄዎች ካሉዎት መጠየቅ ይችላሉ!!"
                tracker.slots["reference_number_am"] = None
                dispatcher.utter_message(text=message)
                dispatcher.utter_template("action_reset_slots_value", tracker)
            except ValueError as e:
                message = "ምንም የበይነመረብ ግንኙነት የለም"
                dispatcher.utter_message(text=message)
                tracker.slots["reference_number_am"] = None
        return [AllSlotsReset()]




class complaintstatusAm(FormAction):
    def name(self) -> Text:
        """Unique identifier of the form"""

        return "form_complaint_status_am"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill"""
        return ["reference_number_am"]
        
    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""
        return {
            "reference_number_am": [
                self.from_text(),

            ],

        }
        print("hhhhhhhhhhhhhhhhhhhhh",reference_number)
   
    def submit(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Define what the form has to do
            after all required slots are filled"""

        
        referencenumber = tracker.get_slot("reference_number_am")
        GlobalVariables.referenceNumber = referencenumber

        session = requests.Session()
        # hostname = "http://196.189.53.206:8089/complaint/response/referenceNumber/"+referencenumber
        hostname = "http://localhost:8089/complaint/response/referenceNumber/"+referencenumber

        url = hostname
        print(url)
        session = requests.Session()
        message = ""
        header = {'Content-type': 'application/json', 'Accept': '*/*'}
        result = True
        if result:

            try:
                
                if connected_to_internet(url=hostname):
                    response_text = session.get(url, headers=header)
                    response_json = json.loads(response_text.text)

                    print("response text is",response_text.text)
                    for data in response_json:
                        dispatcher.utter_message(text=data['content'])
                        dispatcher.utter_message(text=message)
                     
                    if response_json:
                       
                            FollowupAction("utter_additional_slot"),
                            FollowupAction("action_listen")
                         # Reset the slot
              
                    else: 
                        message = "በዚህ ማጣቀሻ ቁጥር ምላሽ አልተሰጠም"
                        dispatcher.utter_message(text=message)
                        
                    dispatcher.utter_message(response="action_reset_slots_value")

                    
                else:
                         response_json = json.loads(response_text.text)
                         print( response_json)
                         message = "በዚህ የትዕዛዝ ቁጥር ትእዛዝ አልተጠየቀም ወይም ቀደም ሲል የተጠየቀ ከሆነ ችግሩ ተቀርፏል"
                
                        
                         return []
                    
             
            except ValueError as e:
                message = "no connection available"
                
            return [SlotSet("referencenumber", referencenumber)]
   






class ActionConfirmComplaint(Action):

    def name(self) -> Text:
        return "action_confirm_complaint"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
   
        referenceNumber = GlobalVariables.referenceNumber
        content = "Empty"
        responseStatus= "AGREED"

        session = requests.Session()
        # hostname = f"http://196.189.53.206:8089/complaint/complainat/referenceNumber/{referenceNumber}/{responseStatus}/{content}"
        hostname = f"http://localhost:8089/complaint/complainat/referenceNumber/{referenceNumber}/{responseStatus}/{content}"

        url = hostname
        entryDate = date.today()
        message = ""
        result = True
        if result:
            try:
               if connected_to_internet(url=hostname):
                    response_text = session.get(url)
                    print("checking")
                    response_json = json.loads(response_text.text)
                    dispatcher.utter_message(" ከእኛ ጋር ጊዜዎን እናደንቃለን.")
                    # reference_number = (response_json['referenceNumber'])
                    # print(reference_number)
                    dispatcher.utter_message(" ቅሬታህን ተቀብለናል። ለሚመለከተው ክፍል እናደርሳለን .")
               else:
                message = "ይቅርታ፣ ለጊዜው ይህን ሂደት ማከናወን አልችልም! ስለዚህ ሌሎች ጥያቄዎች ካሉዎት መጠየቅ ይችላሉ!!"
                tracker.slots["reference_number_am"] = None
                dispatcher.utter_message(text=message)
                dispatcher.utter_template("action_reset_slots_value", tracker)
            except ValueError as e:
                message = "ምንም የበይነመረብ ግንኙነት የለም"
                dispatcher.utter_message(text=message)
                tracker.slots["reference_number_am"] = None
        return [AllSlotsReset()]

    


    
class ReapplycomplinatAm(FormAction):
    """Example of a custom form action"""

    def name(self) -> Text:
        """Unique identifier of the form"""

        return "action_DISAGREED_complaint"

    @staticmethod
    
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill"""
        return ["content"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""
        return {
         
            "content":[
               self.from_text(),
            ],
        }


    def submit(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Define what the form has to do
            after all required slots are filled"""
        # referenceNumber=tracker.latest_message.get("text")
        # global referenceNumber
        referenceNumber = GlobalVariables.referenceNumber
        content = tracker.get_slot("content")
        responseStatus= "DISAGREED"

        session = requests.Session()
        # hostname = f"http://196.189.53.206:8089/complaint/complainat/referenceNumber/{referenceNumber}/{responseStatus}/{content}"
        hostname = f"http://localhost:8089/complaint/complainat/referenceNumber/{referenceNumber}/{responseStatus}/{content}"

        url = hostname
        entryDate = date.today()
        message = ""
        result = True
        if result:
            try:
               if connected_to_internet(url=hostname):
                    response_text = session.get(url)
                    print("checking")
                    response_json = json.loads(response_text.text)
                    dispatcher.utter_message(" ከእኛ ጋር ጊዜዎን እናደንቃለን.")
                    # reference_number = (response_json['referenceNumber'])
                    # print(reference_number)
                    dispatcher.utter_message(" ቅሬታህን ተቀብለናል። ለሚመለከተው ክፍል እናደርሳለን .")
               else:
                message = "ይቅርታ፣ ለጊዜው ይህን ሂደት ማከናወን አልችልም! ስለዚህ ሌሎች ጥያቄዎች ካሉዎት መጠየቅ ይችላሉ!!"
                tracker.slots["reference_number_am"] = None
                dispatcher.utter_message(text=message)
                dispatcher.utter_template("action_reset_slots_value", tracker)
            except ValueError as e:
                message = "ምንም የበይነመረብ ግንኙነት የለም"
                dispatcher.utter_message(text=message)
                tracker.slots["reference_number_am"] = None
        return [AllSlotsReset()]



class case_tracking(FormAction):
    def name(self) -> Text:
        """Unique identifier of the form"""

        return "form_Case_tracking_am"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill"""
        return ["case_status_menu_am"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""
        return {
            "case_status_menu_am": [
                self.from_text(),

            ],
        }

    def submit(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Define what the form has to do
            after all required slots are filled"""
        
        print("gebtoal")
        caseNumber = tracker.get_slot("case_status_menu_am")
        session = requests.Session()
        hostname = "http://213.55.79.158:8080/api/SearchCase?caseNumber=00/0001/"+caseNumber
        url = hostname
        print(url)
        session = requests.Session()
        message = ""
        header = {'Content-type': 'application/json', 'Accept': '*/*'}

        result = True
        if result:
            try:
                

                if connected_to_internet(url=hostname):
                    response_text = session.get(url, headers=header)
                    response_json = json.loads(response_text.text)
                    print("response text is",response_text.text)                    

                    if response_json['CaseNumber']== 404:
                        message = "ለተመረጠው መያዣ ቁጥር ምንም መረጃ የለም"
                        SlotSet("case_status_menu_am", None),
                        dispatcher.utter_message(text=message)
                    
                    else:
                        response_json = json.loads(response_text.text)
                        print( response_json)
                        result="CaseNumber: "+response_json['CaseNumber']+"\n"+ "Plaintiff: "+ response_json['Plaintiff']+"\n"+"Defendant: "+response_json['Defendant']+"\n"+"Bench: "+response_json['Bench']+"\n"+"WhoWon: "+response_json['WhoWon']+"\n"+"DecisionCompared: "+response_json['DecisionCompared']
                   
                        message = "የእርስዎ ጉዳይ ሁኔታ ነው:  {}".format(

                        result)                           
                        dispatcher.utter_message(text=message)
                        SlotSet("case_status_menu_am", None),

                                 
                else:
                    message = "ለጊዜው ይህን ሂደት ማከናወን አልችልም!!"
                    dispatcher.utter_message(text=message)
                    dispatcher.utter_template("action_reset_slots_value", tracker)
            except ValueError as e:
                message = ""
                dispatcher.utter_message(text=message)

        else:
            dispatcher.utter_message(text=message)
        return [AllSlotsReset()]
