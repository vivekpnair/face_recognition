import datetime
import json
import sqlite3
from binascii import a2b_base64

from flask import Flask, render_template, request

# FR
from PIL import Image
import face_recognition
import numpy

import io
import base64

app = Flask(__name__)



def get_db_connection():
    conn = sqlite3.connect('studb.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')  # client side face auth html rendering
def index():
    return render_template('faceauth.html')


@app.route('/studreg_page')  # client side stu reg html rendering
def studreg_page():
    return render_template('regstud.html')


@app.route('/studreg', methods=['POST'])  # server side stu reg rest endpoint
def studreg():
    try:
        req_json = request.json
        profileImg = req_json['imgb64']
        std_name = req_json['std_name']
        std_year = req_json['std_year']
        std_branch = req_json['std_branch']
        std_sem = req_json['std_sem']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("insert into student (name, branch, year, sem) values(?,?,?,?)",
                    (std_name, std_branch, std_year, std_sem))
        std_id = cur.lastrowid
        photo_file = "./profile_pics/" + str(std_id) + ".jpg"
        cur.execute("update student set photo_file=? where stdid=?", (photo_file, std_id))
        conn.commit()
        # save profile image to right path
        binary_data = a2b_base64(profileImg.split(',')[1])  # take the base64 part from datauri string
        fd = open(photo_file, 'wb')
        fd.write(binary_data)
        fd.close()

        cur.close()
        conn.close()
        return {"result": 200, "error": "None", "data": std_id}

    except Exception as e:
        print(e)
        return {"result": 500, "error": "User reg Failed"}


@app.route('/atten_report_page')  # client side atten report html rendering
def atten_report_page():
    return render_template('atten_report.html')


@app.route('/atten_report', methods=['POST'])  # server side atten report rest endpoint
def atten_report():
    try:
        req_json = request.json

        std_id = req_json['std_id']

        conn = get_db_connection()
        cur = conn.cursor()
        rows = cur.execute('select * from attendance where stu_id = ?', [std_id]).fetchall()
        print(rows)
        cur.close()
        conn.close()
        json_rows = json.dumps([dict(ix) for ix in rows])  # CREATE JSON
        return {"result": 200, "error": "None", "data": json_rows}

    except Exception as e:
        print(e)
        return {"result": 500, "error": "User reg Failed"}


@app.route('/authuser', methods=['POST'])
def authuser():
    try:
        req_json = request.json
        checkinImg = req_json['imgb64']
        stdid = req_json['stdid']
        # get student details from db based on stu id
        conn = get_db_connection()
        cur = conn.cursor()
        student = cur.execute('select * from student where stdid = ?', [stdid]).fetchone()
        profile_pic_path = student['photo_file']
        print(profile_pic_path)

        picture_of_me = face_recognition.load_image_file(profile_pic_path)
        my_face_encoding = face_recognition.face_encodings(picture_of_me)[0]

        imgRaw = Image.open(io.BytesIO(base64.b64decode(
            checkinImg.split(',')[1])))  # since  data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD....
        checkinEncoding = face_recognition.face_encodings(numpy.array(imgRaw))
        results = face_recognition.compare_faces([my_face_encoding], checkinEncoding[0])

        if results[0]:
            print("success")
            cur.execute("insert into attendance (stu_id, date, present) values(?,?,?)",
                        (stdid, datetime.datetime.now(), 1))
            conn.commit();
            cur.close();
            conn.close()
            return {"result": 200, "error": "None"}
        else:
            print("failed!")
            cur.close();
            conn.close()
            return {"result": 401, "error": "Auth Failed"}
    except Exception as e:
        print(e)
        return {"result": 401, "error": "Auth Failed"}


# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)