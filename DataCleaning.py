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
def file_data_cleaning():
    #memulai upload
    fileUpload = request.files['fileUpload']
    fileName = fileUpload.filename
    fileNameExt = re.findall(r'[.]\w+',fileName)
    if fileNameExt[0] == ".csv":
        #membaca file yang telah diupload
        df = pd.read_csv(fileUpload, encoding='latin-1')
        #mencari data yang bisa dilakukan cleaning
        
        df_type = df.dtypes.to_list()
        df_columns = df.columns.to_list()
        #df_newColl = pd.DataFrame()
        #df_newColl_list = []
        i = 0

        for i in range (i,len(df_type)) :
            if df_type[i] == "object":
                tobecleaned = df[df_columns[i]]
                cleanedTweet = tobecleaned.replace(r'[^0-9A-Za-z]',' ',regex=True).astype('str')
                cleanTwList = cleanedTweet.to_list()
                cleanTwList = [x.strip(' ') for x in cleanTwList] #menghilangkan spasi yang tidak penting
                cleanTwList = [re.sub(r'\s+',' ',x) for x in cleanTwList] #menghilangkan spasi yang berlebihan
                i += 1
            else:
                pass
        return cleanTwList

if __name__ == '__main__':
    app.run()