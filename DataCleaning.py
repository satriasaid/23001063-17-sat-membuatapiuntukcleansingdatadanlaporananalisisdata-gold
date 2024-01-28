import re, sqlite3
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
        
        #membuat database untuk pre-processed data
        conn_pre = sqlite3.connect('preprocessed_tweet.db')
        c_pre = conn_pre.cursor()
        c_pre.execute('''CREATE TABLE tweet_pre (Tweet varchar(1000), HS INT, Abusive INT, HS_Individual INT, HS_Group INT, HS_Religion INT, HS_Race INT, HS_Physical INT, HS_Gender INT, HS_Other INT, HS_Weak INT, HS_Moderate INT, HS_Strong INT)''')
        df.to_sql('tweet_pre', conn_pre, if_exists='append', index = False)
        
        #STEP 1 : SMOOTH NOISY DATA AND RESOLVE CONSISTENCY

        df_type = df.dtypes.to_list()
        df_columns = df.columns.to_list()
        i = 0
        typeCount = 0
        error_list = []

        #Mengecek apakah jumlah kolom yang harus dilakukan cleaning lebih dari 1
        for type in df_type:
            if type == "object":
                typeCount += 1

        if typeCount == 1 :
            for i in range (i,len(df_type)) :
                if df_type[i] == "object":
                    tobecleaned = df[df_columns[i]]
                    cleanedTweet = tobecleaned.replace(r'(\\x\S+)','',regex=True).astype('str')
                    cleanedTweet = cleanedTweet.replace(r'((\s{2}))',' ',regex=True).astype('str')
                    cleanedTweet = cleanedTweet.replace(r'(\\n)',' ',regex=True).astype('str')
                    cleanedTweet = cleanedTweet.replace(r'(?:RT\W+)',' ',regex=True).astype('str')
                    cleanedTweet = cleanedTweet.replace(r'(?:USER\W+)',' ',regex=True).astype('str')
                    cleanedTweet = cleanedTweet.replace(r'(?:USER)',' ',regex=True).astype('str')
                    cleanedTweet = cleanedTweet.replace(r'(?:https:)\S+',' ',regex=True).astype('str')
                    cleanedTweet = cleanedTweet.replace(r'(?:http)\S+',' ',regex=True).astype('str')
                    cleanedTweet = cleanedTweet.replace(r'(?:https)\S+',' ',regex=True).astype('str')
                    cleanedTweet = cleanedTweet.replace(r'(?:URL)',' ',regex=True).astype('str')
                    cleanedTweet = cleanedTweet.replace(r'[^0-9A-Za-z]',' ',regex=True).astype('str')
                    cleanTwList = cleanedTweet.to_list()
                    cleanTwList = [x.strip(' ') for x in cleanTwList] #menghilangkan spasi yang tidak penting
                    cleanTwList = [re.sub(r'\s+',' ',x) for x in cleanTwList] #menghilangkan spasi yang berlebihan
                    i += 1

                    #membuat database untuk post-processed data
                    df_temp = df
                    df_temp['Tweet'] = cleanTwList

                    #menghilangkan null dan duplicates
                    df_temp = df_temp.dropna()
                    df_temp = df_temp[df_temp['Tweet'] != '']
                    df_temp = df_temp.drop_duplicates()

                    #mengganti kata alay menjadi baku
                    df_alay = pd.read_csv("new_kamusalay.csv", encoding='latin-1', names=['Alay','Normal'])
                    alay_list = df_alay['Alay'].to_list()
                    normal_list = df_alay['Normal'].to_list()

                    tw_alay = df_temp['Tweet']
                    tw_alay_lower = tw_alay.str.lower()

                    dup_tw_alay_lower = tw_alay_lower
                    for i in range(len(alay_list)):
                        tw_normal = dup_tw_alay_lower.replace(r'\b'+ alay_list[i] + r'\b',normal_list[i],regex=True).astype('str')
                        i += 1
                        dup_tw_alay_lower = tw_normal
                    
                    #melakukan sensorship abusive language
                    df_abusive = pd.read_csv("abusive.csv")
                    abusive_list = df_abusive['ABUSIVE'].to_list()

                    for i in range(len(abusive_list)):
                        tw_normal = dup_tw_alay_lower.replace(r'\b'+ abusive_list[i] + r'\b','(sensor)',regex=True).astype('str')
                        i += 1
                        dup_tw_alay_lower = tw_normal

                    #meletakkan data hasil cleaning ke df_temp['Tweet']
                    df_temp['Tweet'] = dup_tw_alay_lower

                    #mengubah df_temp['Tweet'] ke dalam suatu list
                    finalCleanTwList = df_temp['Tweet'].to_list()

                    conn_post = sqlite3.connect('postprocessed_tweet.db')
                    c_post = conn_post.cursor()
                    c_post.execute('''CREATE TABLE tweet_post (Tweet varchar(1000), HS INT, Abusive INT, HS_Individual INT, HS_Group INT, HS_Religion INT, HS_Race INT, HS_Physical INT, HS_Gender INT, HS_Other INT, HS_Weak INT, HS_Moderate INT, HS_Strong INT)''')
                    df_temp.to_sql('tweet_post', conn_post, if_exists='append', index = False)

                else:
                    pass
        else:
            error_colnum = "The uploaded file has more than 1 column to clean!"
            error_list.append(error_colnum)
            return error_list

        return finalCleanTwList
    
    else:
        error_notCSV = "the uploaded file is not CSV"
        error_list.append(error_notCSV)
        return error_list
    
if __name__ == '__main__':
    app.run()