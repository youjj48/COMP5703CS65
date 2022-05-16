import tkinter
from tkinter import *
from tkinter import ttk
import tkinter.messagebox
import os
import multiprocessing
import json
from scrapy import cmdline

def startProcess(key):
    mp = multiprocessing.Process(target=startSpider,args=(key,))
    mp.start()
    initItem(mp,key)
    
def startSpider(key):
    if key == "MayoClinic":
        cmdline.execute("scrapy crawl mayo -o mayo.json".split())
    elif key == "MedlinePlus":
        cmdline.execute("scrapy crawl medline -o medline.json".split())
        
def initItem(mp,key):
    pid = mp.pid
    name = key
    status = 'running'
    existing_data_count = 0
    if key == 'MayoClinic':
        if os.path.exists('./mayo.json'):
            with open('./mayo.json','r',encoding='utf8')as fp:
                json_data = json.load(fp)
            existing_data_count = len(json_data)
            os.remove('./mayo.json')
        if os.path.exists('./mayo_config.txt'):
            os.remove('./mayo_config.txt')

    elif key == 'MedlinePlus':
        if os.path.exists('./medline.json'):
            with open('./medline.json','r',encoding='utf8')as fp:
                json_data = json.load(fp)
            existing_data_count = len(json_data)
            os.remove('./medline.json')
        if os.path.exists('./medline_config.txt'):
            os.remove('./medline_config.txt')
            
    elif key == 'HealthDirect':
        status = 'To be implemented'
        
    #print("initialization finished")
    return tree.insert('',0,values=(pid,name,status,existing_data_count,0))

def loopUpdateItem():
    for ele in tree.get_children():
        if tree.item(ele)['values'][1] == 'MayoClinic':
            if os.path.exists('./mayo_config.txt'):
                with open('./mayo_config.txt','r',encoding='utf8')as fp: 
                    obtained_data_count = int(fp.readline())
                if tree.item(ele)['values'][4] == obtained_data_count:
                    status = 'finished'
                    #update status
                    tree.item(ele,values=(
                        tree.item(ele)['values'][0],
                        tree.item(ele)['values'][1],
                        status,
                        tree.item(ele)['values'][3],
                        tree.item(ele)['values'][4],
                    ))
                    
                else:
                    status = 'running'
                    #update obtained data count
                    tree.item(ele,values=(
                        tree.item(ele)['values'][0],
                        tree.item(ele)['values'][1],
                        status,
                        tree.item(ele)['values'][3],
                        obtained_data_count,
                    ))
        elif tree.item(ele)['values'][1] == 'MedlinePlus':
            if os.path.exists('./medline_config.txt'):
                with open('./medline_config.txt','r',encoding='utf8')as fp: 
                    obtained_data_count = int(fp.readline())
                if tree.item(ele)['values'][4] == obtained_data_count:
                    status = 'finished'
                    #update status
                    tree.item(ele,values=(
                        tree.item(ele)['values'][0],
                        tree.item(ele)['values'][1],
                        status,
                        tree.item(ele)['values'][3],
                        tree.item(ele)['values'][4],
                    ))
                    
                else:
                    #update obtained data count
                    tree.item(ele,values=(
                        tree.item(ele)['values'][0],
                        tree.item(ele)['values'][1],
                        tree.item(ele)['values'][2],
                        tree.item(ele)['values'][3],
                        obtained_data_count,
                    ))
    root.after(2000,loopUpdateItem)
if __name__ == '__main__':

    root = tkinter.Tk()
    value  = StringVar()
    value.set('MayoClinic')
    values = ['MayoClinic','HealthDirect','MedlinePlus']
    textbox = ttk.Combobox(
        master = root,
        height = 10,
        width = 20,
        state = 'readonly',
        font = ('',20),
        textvariable = value,
        values = values
    )
    tree = ttk.Treeview(root,show='headings',columns=('PID','Name','Status','Existing Data','Obtained Data'))
    ysb = ttk.Scrollbar(root,orient='vertical',command=tree.yview)
    xsb = ttk.Scrollbar(root,orient='horizontal',command=tree.xview)
    tree.configure(yscroll=ysb.set,xscroll=xsb.set)
    
    tree.column('PID',anchor='center')
    tree.column('Name',anchor='center')
    tree.column('Status',anchor='center')
    tree.column('Existing Data',anchor='center')
    tree.column('Obtained Data',anchor='center')
    tree.heading('PID',text='PID')
    tree.heading('Name',text='Name')
    tree.heading('Status',text='Status')
    tree.heading('Existing Data',text='Existing Data')
    tree.heading('Obtained Data',text='Obtained Data')
    #vbar = ttk.Scrollbar(root,orient=VERTICAL,command=tree.yview)
    #tree.configure(yscrollcommand=vbar.set)

    textbox.grid(row=3)
    tree.grid(row=5)
    #Click the Button to call startProcess, a new progress will be built to run scrapy crawler.
    tkinter.Button(root,text="start crawling",command=lambda : startProcess(textbox.get())).grid(row=4)
    loopUpdateItem()
    root.mainloop()