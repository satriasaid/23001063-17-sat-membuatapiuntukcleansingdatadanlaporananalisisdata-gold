import re
import pandas as pd
from flask import Flask, jsonify, request
from flasgger import Swagger, LazyString, LazyJSONEncoder, swag_from

class CustomFlaskAppWithEncoder(Flask):
    json_provider_class = LazyJSONEncoder

app = CustomFlaskAppWithEncoder(__name__)

swagger_template = dict(
    info = {
        'title' : LazyString(lambda: 'API untuk Cleansing Data dan Laporan Analisis Data'),
        'version' : LazyString(lambda: '1.0.0'),
        'description' : LazyString(lambda: 'API untuk Cleansing data dan Laporan Analisis Data'),
    },
    host = LazyString(lambda: request.host),
)

swagger_config = {
    'headers' : [],
    'specs' : [
        {
            "endpoint" : "docs",
            "route" : "/docs.json",
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/", 
}
swagger = Swagger(app, template = swagger_template, config = swagger_config)

@swag_from("docs/hello_world.yml", methods=['GET'])
@app.route('/', methods=['GET'])
def hello_world():
    json_response = {
        'status_code' : 200,
        'description' : "Menyapa Hello World",
        'data' : "Hello World",
    }
    
    response_data = jsonify(json_response)
    return response_data

#Endpoint untuk membersihkan data dari form
@swag_from("docs/formDataCleaning.yml", methods=['POST'])
@app.route('/form-data-cleaning',methods=['POST'])
def form_data_cleaning():

    text = request.form.get('text')

    json_response = {
        'status_code' : 200,
        'description' : "Teks yang sudah diproses",
        'data' : re.sub(r'[^a-zA-Z0-9]',' ',text)        
    }

    response_data = jsonify(json_response)
    return response_data

@swag_from("docs/fileDataCleaning.yml", methods=['POST'])
@app.route('/file-data-cleaning',methods=['POST'])
def form_data_cleansing():
    
    #memulai upload
    fileUpload = request.files['fileUpload']
    #fileName = fileUpload.filename
    
    #membaca file yang telah diupload
    df = pd.read_csv(fileUpload, encoding='latin-1')

    #mencari data yang bisa dilakukan cleaning
    tbc = df['Tweet']
    cleanedTweet = tbc.replace(r'[^0-9A-Za-z]',' ',regex=True).astype('str')
    cleanTwList = cleanedTweet.to_list()
    return cleanTwList

if __name__ == '__main__':
    app.run()
