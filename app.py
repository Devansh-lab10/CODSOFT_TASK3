from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3, os
from werkzeug.utils import secure_filename

app=Flask(__name__)
app.secret_key=os.environ.get('SECRET_KEY','dev-secret-change-this')
app.config['UPLOAD_FOLDER']=os.path.join(app.root_path,'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'],exist_ok=True)
DB=os.path.join(app.root_path,'careerhub.db')

def connect():
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row; con.execute('PRAGMA foreign_keys=ON'); return con
def query_db(sql,args=()):
    with connect() as con: return con.execute(sql,args).fetchall()
def execute_db(sql,args=()):
    with connect() as con: con.execute(sql,args); con.commit()

def init_db():
    with connect() as con:
        con.executescript("\nCREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, company TEXT NOT NULL, location TEXT NOT NULL, type TEXT NOT NULL, description TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);\nCREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER NOT NULL, applicant TEXT NOT NULL, email TEXT NOT NULL, resume TEXT, status TEXT DEFAULT 'Applied', created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(job_id) REFERENCES jobs(id));\n")
        con.executescript("INSERT OR IGNORE INTO jobs(id,title,company,location,type,description) VALUES\n(1,'Junior Python Developer','BrightByte','Remote','Full-time','Build and maintain Python web applications using Flask and SQL.'),\n(2,'Frontend Intern','PixelWorks','Noida, India','Internship','Create responsive interfaces with HTML, CSS and JavaScript.'),\n(3,'Data Analyst Intern','Insight Labs','Hybrid','Internship','Analyze datasets, prepare reports and communicate findings.');")
        con.commit()


@app.route('/')
def home():
    q=request.args.get('q','')
    jobs=query_db("SELECT * FROM jobs WHERE title LIKE ? OR company LIKE ? OR location LIKE ? ORDER BY id DESC",(f'%{q}%',f'%{q}%',f'%{q}%'))
    apps=query_db("SELECT a.*,j.title FROM applications a JOIN jobs j ON j.id=a.job_id ORDER BY a.id DESC")
    return render_template('home.html',jobs=jobs,apps=apps,q=q)
@app.route('/jobs/add',methods=['POST'])
def job_add():
    execute_db("INSERT INTO jobs(title,company,location,type,description) VALUES(?,?,?,?,?)",(request.form['title'],request.form['company'],request.form['location'],request.form['type'],request.form['description']))
    flash('Job published.','success'); return redirect(url_for('home'))
@app.route('/jobs/<int:jid>/apply',methods=['POST'])
def apply(jid):
    resume=''
    f=request.files.get('resume')
    if f and f.filename:
        safe=secure_filename(f.filename)
        if not safe.lower().endswith(('.pdf','.doc','.docx')): flash('Resume must be PDF or Word.','danger'); return redirect(url_for('home'))
        f.save(os.path.join(app.config['UPLOAD_FOLDER'],safe)); resume=safe
    execute_db("INSERT INTO applications(job_id,applicant,email,resume) VALUES(?,?,?,?)",(jid,request.form['applicant'],request.form['email'],resume))
    flash('Application submitted.','success'); return redirect(url_for('home'))
@app.route('/applications/<int:aid>/status',methods=['POST'])
def application_status(aid):
    execute_db("UPDATE applications SET status=? WHERE id=?",(request.form['status'],aid)); flash('Application status updated.','success'); return redirect(url_for('home'))


if __name__=='__main__':
    init_db()
    app.run(debug=True,port=5003)
