import requests
import json
import time
import sys
import os
import base64
from urllib.parse import urlparse, urlsplit

class ExecuteOnDivaServices:

    def main(self):
        """This method executes a binarization method on DIVAServices the script can be executed as follows:
            python executeOnDivaservices.py URL_TO_METHOD PATH_TO_INPUT_IMAGE PATH_TO_OUTPUT_FOLDER
        """
        if(len(sys.argv) < 3):
            sys.stderr.write('The method needs 3 parameters!')
            exit()
        url = sys.argv[1]
        base_url = urlsplit(url).netloc
        input_image = sys.argv[2]
        output_folder = sys.argv[3]

        # Upload the Image to DIVAServices
        image_identifier = self.uploadImage(base_url,input_image)
        # Start the binarization process
        resultLink = self.runBinarization(url, image_identifier)
        print("start polling for results at: " + resultLink)
        # Poll for the result
        result = self.pollResult(resultLink)
        # Download the result image
        self.saveFile(result['output'][0]['file']['url'],output_folder)
        
    def uploadImage(self, base_url,input_image):
        """Uploads an image to DIVAServices
        
        Arguments:
            input_image {string} -- The path to the input image to use
        
        Returns:
            string -- the DIVAServices identifier of the uploaded image
        """ 

        url = "http://" + base_url + "/collections"
        with open(input_image, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('ascii')
            file_name = os.path.basename(input_image)
            payload = "{\"files\":[{\"type\":\"image\",\"value\":\"" + encoded_string +  "\",\"name\":\"" + file_name.split('.')[0] + "\"}]}"
            headers = {
                'content-type': "application/json"
            }
            response = json.loads(requests.request("POST", url, data=payload, headers=headers).text)
            return response['collection'] + "/" + file_name

    def runBinarization(self, url, input_image):
        """ Runs a binarization method
        
        Arguments:
            url {string} -- The URL to the binarization method
            input_image {string} -- The DIVAServices identifier of the input image
        
        Returns:
            string -- the result link at which the result will be available
        """

        payload = "{\"parameters\":{},\"data\":[{\"inputImage\": \"" + input_image + "\"}]}"
        headers = {
            'content-type': "application/json"
        }

        response = requests.request("POST", url, data=payload, headers=headers)
        json_data = json.loads(response.text)
        return json_data['results'][0]['resultLink']

    
    def pollResult(self, result_link):
        """ Polls for the result of the execution in 1s intervals
        
        Arguments:
            result_link {string} -- [the resultLink generated by the POST request that started the execution]
        
        Returns:
            [json] -- [the result of the execution]
        """

        response = json.loads(requests.request("GET", result_link).text)
        while(response['status'] != 'done'):
            print("current status: " + response['status'])
            if(response['status'] == 'error'):
                sys.stderr.write('Error in executing the request. See the log file at: ' + response['output'][0]['file']['url'])
                sys.exit()
            time.sleep(1)
            response = json.loads(requests.request("GET", result_link).text)

        return response

    def saveFile(self, url, output_folder):
        """Saves a file from a URL into a local folder
        
        Arguments:
            url {string} -- The URL from where to download the file
            output_folder {string} -- The path to the output directory
        """

        # open in binary mode
        filename = os.path.basename(urlparse(url).path)
        with open(output_folder + filename, "wb") as file:
            # get request
            response = requests.get(url)
            # write to file
            file.write(response.content)


if __name__ == "__main__":
    ExecuteOnDivaServices().main()
