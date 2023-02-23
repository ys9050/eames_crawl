import json
import pprint
import urllib3
from html.parser import HTMLParser

MAIN_URL = "https://www.hermanmiller.com/ComApproval/"
FAMILY_URL = "https://www.hermanmiller.com/ComApproval/families?sId="
FABRIC_URL = "https://www.hermanmiller.com/ComApproval/testResults?testNbr="

supplier_code = []
supplier_name = []
supplier_dict = {}

family_code = []
family_name = []
family_dict = {}

total_dict = {}
eames_pass_dict = {}
eames_fail_dict = {}

current_fabric = ""

class SupplierParse(HTMLParser):
    supplier_flag = False

    def __init__(self):
        super().__init__()
        self.reset()

    def handle_starttag(self, tag, attrs):
        # Only parse the 'anchor' tag.
        if tag == "option":
           for (_, code) in attrs:
               if code != None and code != '':
                   supplier_code.append(code)
                   self.supplier_flag = True

    def handle_data(self, data):
        if self.supplier_flag:
            supplier_name.append(" ".join(data.split()))
            self.supplier_flag = False

class FamilyParse(HTMLParser):
    family_flag = False

    def __init__(self):
        super().__init__()
        self.reset()

    def handle_starttag(self, tag, attrs):
        for (_, code) in attrs:
            if code != None and code != '':
                family_code.append(code)
                self.family_flag = True

    def handle_data(self, data):
        if self.family_flag:
            family_name.append(" ".join(data.split()))
            self.family_flag = False

class EamesParse(HTMLParser):
    global current_fabric
    global total_dict
    global eames_pass_dict
    global eames_fail_dict

    eames_flag = False
    def __init__(self):
        super().__init__()
        self.reset()

    def handle_starttag(self, tag, attrs):
        # print(tag)
        if tag == "span" and self.eames_flag:
            self.eames_flag = False
            for (key, code) in attrs:
                if code != None and code != '':
                    total_dict[current_fabric] = code
                    if code == 'pass':
                        eames_pass_dict[current_fabric] = code
                    if code == 'fail':
                        eames_fail_dict[current_fabric] = code

    def handle_data(self, data):
        if "Eames Lounge" in data:
            print("Eames Lounge detected")
            self.eames_flag = True

def fetch_supplier():
    global supplier_dict
    parser = SupplierParse()

    http = urllib3.PoolManager()
    r = http.request('GET', MAIN_URL)
    strR = str(r.data)
    parser.feed(strR)
    if len(supplier_code) == len(supplier_name):
        supplier_dict = dict(zip(supplier_name, supplier_code))
    print("Finished fetching suppliers")

def fetch_family():
    global supplier_dict
    global family_dict
    global family_code
    global family_name
    parser = FamilyParse()

    # count = 0
    for (name, code) in supplier_dict.items():
        print("Looking at " + name)
        # if count > 10:
        #     break
        # count += 1
        family_url = FAMILY_URL+code
        http = urllib3.PoolManager()
        r = http.request('GET', family_url)
        parser = FamilyParse()
        strR = str(r.data)
        parser.feed(strR)
        # Update family name to have company name
        for i in range(len(family_name)):
            family_name[i] = name + " " + family_name[i]
        temp_family_dict = dict(zip(family_code, family_name))
        family_dict = {**temp_family_dict, **family_dict}
        family_code = []
        family_name = []
    print("Finished fetching family fabrics")

def fetch_eames():
    global family_dict
    global total_dict
    global current_fabric
    parser = EamesParse()

    count = 0
    dict_count = len(family_dict)
    for (code, name) in family_dict.items():
        current_fabric = name
        count += 1
        print("Looking at " + name + " " + str(count) + "/" + str(dict_count))
        fabric_url = FABRIC_URL+code
        http = urllib3.PoolManager()
        r = http.request('GET', fabric_url)
        strR = str(r.data)
        parser.feed(strR)
    pprint.pprint(total_dict)

def write():
    global total_dict
    global eames_pass_dict
    global eames_fail_dict

    result = json.dumps(total_dict, indent=4)
    f = open("eames.txt", "a")
    f.write(result)
    f.close()

    result = json.dumps(eames_pass_dict, indent=4)
    f = open("eames_pass.txt", "a")
    f.write(result)
    f.close()

    result = json.dumps(eames_fail_dict, indent=4)
    f = open("eames_fail.txt", "a")
    f.write(result)
    f.close()

def main():
    fetch_supplier()
    fetch_family()
    fetch_eames()
    write()
    # pprint.pprint(family_dict)

if __name__ == '__main__':
    main()
