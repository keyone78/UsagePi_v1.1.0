 #!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# Date : JUNE 29 2016
# Project Name: piUsage v1.0.0   
# About : This project is to measure water usage in term of dollar and cents 
# Built in feature: Generate report daily, weekly and monthly
#                 : Send report via email
#                 : Currently only support singpaore domestic water bill
#
# Aurthor: Lew Kee Wan 
#
#
#
#
#---------------------------------------------------------
# IMPORT LIB
#---------------------------------------------------------
import Tkinter as Tk
import RPi.GPIO as pi
import time
import datetime
import random
import smtplib
import mimetypes
import csv
import logging
from datetime import  date, timedelta
from dateutil.relativedelta import relativedelta
from colorama import *
from sys import argv
from email.mime.text  import MIMEText
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.base import MIMEBase
from email.message import Message
#---------------------------------------------------------
# GPIO SETTING, pin input and output
#---------------------------------------------------------
gpio_modes = ("Output","Input")

pi.setmode(pi.BCM)   # using BCM mode
pi.setup(17, pi.IN, pull_up_down=pi.PUD_UP)   # pull up resistor
pi.setwarnings(False)

#---------------------------------------------------------
# COLOR CODE FOR EMAIL
#---------------------------------------------------------
ATOMIC_TANGERINE="#F9966B"
LIGHTGREEN="#3EA99F"
LIGHT_GOLDENROD = "#FAFAD2"
MANGO_ORAGNE="#A18648"
MUDD_WATER="#A18648"
NEPAL="#95B9C7"
ROSE="#E8ADAA"
SUMMERSKY="#40BFFF"
WHEAT="#F5DEB3"
VANILLA="#F4CCCC"
#---------------------------------------------------------
# EMAIL SETTING 
#---------------------------------------------------------
#.csv header
CSV_HEADER="Date,Month,Year,Day,Time,Usage Cost,Litre"+"\n"
# ENDING MESSAGE
THANKYOU="Thanks for trying this project."
QOUTE="<i>We never know the worth of water till the well is dry.<i><br><b> - Thomas Fuller,MD,1732<b>"

MAIL_SETUP="<h2 style='background-color:"+LIGHT_GOLDENROD+"'>Setup e-mail Sucessfully.</h2> Hi User of uPi,\n<br>\n<br>"
MAIL_SETUP+="<body bgcolor='"+ATOMIC_TANGERINE+"'> </body>"
MAIL_SETUP+=THANKYOU +"\n<br>\n<br>"+ QOUTE

#------------------------------------ 

MAIL_DAILY="<h2 style='background-color:"+ LIGHTGREEN +"'>Water Usage Report : Daily </h2> Hi User of uPi,"
MAIL_DAILY+= "<body bgcolor='"+ VANILLA + "'> </body>"

#------------------------------------ 
MAIL_WEEKLY="<h2 style='background-color:" + LIGHT_GOLDENROD +"'>Water Usage Report : Weekly</h2>\n<br>Hi User of uPi,"
MAIL_WEEKLY+= "<body bgcolor='"+ NEPAL +"'> </body>"

#------------------------------------ 

MAIL_MONTHLY="<h2 style='background-color:"+ROSE+"'>Water Usage Report : Monthly </h2> \n<br>Hi User of uPi,"
MAIL_MONTHLY+= "<body bgcolor='"+WHEAT+"'> </body>"

# -------------------------------------------
# Currently the mail sever is setup using google mail 
# if you want to use other mail server please refer 
#https://www.arclab.com/en/kb/email/list-of-smtp-and-imap-servers-mailserver-list.html
#
#------------------------------------ 
SMTP_SERVER='smtp.gmail.com'
SERVER_NO=587
SENDER='YOURMAIL@gmail.com'
RECEIVER='YOURMAILgmail.com'   # version 1
uPiMail=SENDER                  
password='passwd'          # set your passwd email


#---------------------------------------------------------
# COST VARIABLE 
#---------------------------------------------------------
#COST=0.00 # $0.00
TARIFF=1.17
TARIFF_2=1.40    # if above 4000litres
WATER_CON_TAX=0.30
WATER_CON_TAX_2=0.45
WATER_BR_FEE=0.2803  #$/0.1 litre rate
GST=0.07
#varcost=0.00
#varcostTwo=0.00
#---------------------------------
T_DAY_LITRE=0.0
T_DAY_COST=0.0
T_MOM_LITRE=0.0
T_MOM_COST=0.0
GT_LITRE = 0.0  # Grand total litre of water usage
#---------------------------------
#---------------------------------------------------------
# CONSTANT 
#---------------------------------------------------------
ON=1
OFF=0
STOP=0
GO=1
RESET=0
RUN=1
True=1
False=0
#---------------------------------------------------------
# UI CONSTANT 
#---------------------------------------------------------
HFONT='consolas', 16, 'bold'    # Header font
#---------------------------------------------------------
# FILE CONSTANT 
#---------------------------------------------------------
FILE_HOURLY="piRecHr.csv"
#FILE_DLY_HR="a_piRecDailyHr.csv"
FILE_DAY_WEEKLY="piRecDailyWeekly.csv"
FILE_DAY_MONTHLY="piRecDailyMonth.csv"
FILE_WEEKLY="pirecHisWeek.csv"
#---------------------------------------------------------
# INTERRUPT FLAG 
#---------------------------------------------------------
FLAG_REC=GO
FLAG_PROCESS=STOP

#---------------------------------------------------------
# OTHER 
#---------------------------------------------------------
init(autoreset=True)
#---------------------------------------------------------
# BLANK 
#---------------------------------------------------------
#---------------------------------------------------------
# LOGGER 
#---------------------------------------------------------
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

fh = logging.FileHandler('pilog_.txt')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
#---------------------------------------------------------
#  APP CLASS  
#---------------------------------------------------------

class simpleapp_tk(Tk.Tk):
    def __init__(self,parent):
        Tk.Tk.__init__(self,parent)
        self.parent = parent

        logging.debug('initialize class.')
        self.initialize()
        self.initialize_date()
        self.initialize_WaterTariffInform()
        self.initialize_CostSetting()
        self.initialize_UsageInform()
        self.initialize_Form()
        self.start_sequence_INT()
#---------------------------------------------------------
# INTERRUPT FUNCTION FOR FLOW SENSOR  
#---------------------------------------------------------
    
        def myInterrupt(channel):              # interrpt inside the app class
           self.FLAG_REC=STOP
           self.trigger()
    	   self.reTimer(1000,"FLAG_INT")
           self.FLAG_REC=GO
       # intrreupt by falling edge  
        pi.add_event_detect(17, pi.FALLING,callback=myInterrupt, bouncetime=300)   
	 
    def initialize(self):
        
        logging.debug('initialize start.')
        self.upiemail=Email()       # create email object
        self.grid()
              
        self.upiemail.setup_mail()  # settup up email
        print Fore.CYAN + 'email setup done'
        logging.info('L280: email setup - done')
#---------------------------------------------------------
# UI FOR DATE & TIME 
#---------------------------------------------------------

    def initialize_date(self):
        self.labeldate = Tk.StringVar()
        datelabel = Tk.Label(self,textvariable=self.labeldate, anchor="w", font=(HFONT),fg="black",bg="gold")
        datelabel.grid(column=0,row=0,columnspan=2,sticky='EW')
        localtime   = time.localtime()
	                 	# date time result format : Saturday 10 August 2013     Time  : 20:34:11 HRS
        timeString  = time.strftime("Date: " + "%A %d. %B %Y" +  "    Time : " + "%H :%M :%S HRS", localtime)
        self.labeldate.set( timeString)    # Display to UI
		
#---------------------------------------------------------
# UI FOR WATER TARIFF INFORMATION 
#---------------------------------------------------------
        
    def initialize_WaterTariffInform(self):
#------------------------------------------------------------------		
#                                                          SET TEXT
        wtInform_HText="A: Water Tariff Information"
        wt_TextOne="Domestic :   0 to 40m"+(u"\u00B3")+"   = $1.1700 + 30% WCT + $0.2803 WB.Fee"
        wt_TextTwo="                 Above 40m"+(u"\u00B3")+"  = $1.4000 + 45% WCT + $0.2083 WB.Fee"
        wt_TextThree="WCT :Water Conservation Tax"
        wt_TextFour="WB.Fee :Waterborne Fee ($/m"+(u"\u00B3")+")"
        wt_TextFive="1m"+(u"\u00B3")+" = 1000 litres" 
        wt_TextSix="1 litre = 1000 mililitres" 
#------------------------------------------------------------------		
#                                                     LABEL SETTING
        wt_label_header= Tk.Label(self,text=wtInform_HText, anchor="w", font=(HFONT),fg="white",bg="green")
        wt_label_One = Tk.Label(self,text=wt_TextOne, anchor="w", font=('Times', 15, ))
        wt_label_Two = Tk.Label(self,text=wt_TextTwo, anchor="w", font=('Times', 15, ))
        wt_label_Three = Tk.Label(self,text=wt_TextThree , anchor="e", font=('Times', 13, 'italic'))
        wt_label_Four = Tk.Label(self,text=wt_TextFour , anchor="e", font=('Times', 13, 'italic'))
        wt_label_Five = Tk.Label(self,text=wt_TextFive, anchor="e", font=('Times', 13, 'italic'))
        wt_label_Six = Tk.Label(self,text=wt_TextSix, anchor="e", font=('Times', 13, 'italic'))
        
#------------------------------------------------------------------		
#                                                     LABEL DISPLAY
        wt_label_header.grid(column=0,row=3,rowspan=2,columnspan=2,sticky='EW')
        wt_label_One.grid(column=0,row=5,columnspan=2,sticky='EW')
        wt_label_Two.grid(column=0,row=6,columnspan=2,sticky='EW')
        wt_label_Three.grid(column=0,row=7,columnspan=1,sticky='W')
        wt_label_Four.grid(column=0,row=8,columnspan=1,sticky='W')
        wt_label_Five.grid(column=1,row=7,columnspan=1,sticky='E')
        wt_label_Six.grid(column=1,row=8,columnspan=1,sticky='E')

#---------------------------------------------------------
# COMPUTATION COST  
#---------------------------------------------------------
    def initialize_CostSetting(self):
        self.varcost=((TARIFF + TARIFF * WATER_CON_TAX + WATER_BR_FEE)*(1+GST)) /1000
        self.varcostTwo=((TARIFF_2 + TARIFF_2 * WATER_CON_TAX_2 +WATER_BR_FEE)*(1+GST)) /1000
        self.cnt=0        # variable pulse of flow sensor
        self.litre=39999.0   # variable litre
        self.litreTwo=0.0
        self.GT_litre=39999.0
	print str(self.varcost) + " <-- cost 1"	
	print str(self.varcostTwo) + " <-- cost 2"	
#---------------------------------------------------------
# WATER USAGE INFORMATION  
#---------------------------------------------------------
    
    def initialize_UsageInform(self):
        usage_HText="B: Water Usage Information"

        lineTwolabel = Tk.Label(self,text=usage_HText, font=(HFONT), anchor="w",fg="white",bg="blue")
        lineTwolabel.grid(column=0,row=10,rowspan=3,columnspan=2,sticky='EW')
#------------------------------------------------------------------		
#                                                       TEXT VARIABLE
        pulse_text=" 1) No of Flow Pulse           :"
        litre_text=" 2) No of Litre(s) Used  (L) :"
        cost_text =" 3) Water Usage Cost      S$:"

#------------------------------------------------------------------		
#                                                       PULSE LABEL
        self.pulslabel=Tk.Label(self,text=pulse_text, font=('times', 18,'bold'),padx=-10)
        self.pulslabel.grid(column=0,row=13,columnspan=1,sticky='W')
      
        self.var_pulse = Tk.StringVar()
        self.pulselabel=Tk.Label(self,textvariable=self.var_pulse, font=('times', 22,'bold'),padx=-10)
        
        self.pulselabel.grid(column=1,row=13,columnspan=2,sticky='W')
        self.var_pulse.set('0')   # flow sensor pluse 
#------------------------------------------------------------------		
#                                                       LITRE LABEL
       
        self.litrlabel=Tk.Label(self,text= litre_text, font=('times', 18,'bold'))
        self.litrlabel.grid(column=0,row=14,columnspan=1,sticky='W')
		
        self.var_litre = Tk.StringVar()
        self.litrelabel=Tk.Label(self,textvariable=self.var_litre, font=('times', 24,'bold'))
        self.litrelabel.grid(column=1,row=14,columnspan=1,sticky='W')
        self.var_litre.set('0.0')         ###  litre of water  usage
#------------------------------------------------------------------		
#                                                       COST LABEL
	
        self.coslabel=Tk.Label(self, text=cost_text, font=('times', 18,'bold'))
        self.coslabel.grid(column=0,row=15,columnspan=1,sticky='W')
		
        self.var_cost = Tk.StringVar()
        self.costlabel=Tk.Label(self, textvariable=self.var_cost, font=('times', 30,'bold'))
        self.costlabel.grid(column=1,row=15,columnspan=1,sticky='W')
        self.var_cost.set('0.00')                ### water usage cost 
#---------------------------------------------------------
# CONFIGURE UI SETTING  
#---------------------------------------------------------
		
    def initialize_Form(self):
        self.grid_columnconfigure(1,weight=10)
        self.resizable(False,False)
        w = 660 # width for the Tk root
        h = 380 # height for the Tk root

        # get screen width and height
        ws = self.winfo_screenwidth() # width of the screen
        hs = self.winfo_screenheight() # height of the screen

        # calculate x and y coordinates for the Tk root window
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)

        # set the dimensions of the screen 
        # and where it is placed
        self.geometry('%dx%d+%d+%d' % (w, h, x, y))   #set size and location for screen, will be at centre
        self.minsize(200,220)

#---------------------------------------------------------
# Start the interrupt sequence  tasks 
#---------------------------------------------------------

    def start_sequence_INT(self):
        # UI completed
        print Fore.CYAN + 'UI completed '      
        self.FLAG_REC=GO; 

        # sent monthly alert
        self.monthly_email_int()
        print Fore.GREEN + 'start mail monthly '
      
        # Send weekly alert
        self.weekly_email_int()                     
        print Fore.YELLOW + 'start mail weekly '

        #Send daily alert
        self.daily_email_int()
        print Fore.RED + 'start mail daily '
       
        # trigger hourly record interval
        self.save_record_hourly();  # make first record , will retrigger the save record by timer

######################################################################################################################
######################################################################################################################
######################################################################################################################

#---------------------------------------------------------
# FUNCTION 
#---------------------------------------------------------
        
    def trigger(self): 
        
         self.var_pulse.set(str(self.cnt))
         self.cnt+=1
         showCost=0.0                    #rest cost (locally)
         showLitre=0.0                   #rest litre usage (locally)
         if self.cnt>=9 :                # to set the parameter of pluse use in flow sensor

            self.GT_litre+=0.2           # every 9 pluses/200ml
            if(self.GT_litre<=40000):    # if less than  40 cubic meter
              self.litre+=0.2            # 0.2 litre =200ml
              showLitre=self.litre       
              showCost=self.litre * self.varcost       # compute the cost of water

             # if water usage is  39,999(L) toward 40000.1 (L) 
             # use varcost and varcostTwo to compute water usage
            elif(self.litre !=0) and (self.GT_litre>40000):
              self.litreTwo+=0.2                   
              showLitre = self.litre + self.litreTwo          # print litre of water  
              showCost =(self.litreTwo * self.varcostTwo) + (self.litre*self.varcost  )

            # if GT_litre > 40 cubic meter then only use varcostTwo to compute 
            else:                     # over  40 Cubic meter
              self.GT_litre+=0.2
              self.litreTwo+=0.2   
              showLitre = self.litreTwo  
              showCost = (self.litreTwo * self.varcostTwo)
           
           # Display to UI  
            self.var_litre.set(str(showLitre))       # print litre of water  
            self.var_cost.set(str(showCost))         # print the ost out 
            self.cnt=0                               # reset the cnt
#---------------------------------------------------------
# FUNCTION : EMAIL 
#---------------------------------------------------------
  
    def pre_sendmail_monthly(self):   
        if(self.FLAG_REC==GO):
            
            print Fore.GREEN + 'pre_sendmail MONTHLY'
            # compute the monthly data 
            self.computation(FILE_DAY_MONTHLY,30)     
             # prepare message block
            mailMsg=self.mail_MsgBlk(self.T_MOM_LITRE, self.T_MOM_COST,30)    
           # transfer to monthly temp file
            self.trFileMth(FILE_DAY_MONTHLY,"t"+FILE_DAY_MONTHLY)   
             # attach monthly temp file to mail
            self.upiemail.setup_mail2(mailMsg,"Monthly Water Usage","t"+FILE_DAY_MONTHLY) 
             # clear the temp file 
            self.clearFile("t"+FILE_DAY_MONTHLY)   
            # achived purpose
            self.saveFile("a"+self.timeStamp("T2")+FILE_DAY_MONTHLY, str(self.T_MOM_LITRE)+","+str(self.T_MOM_COST))   
            logging.info('pre_sendmail_monthly - done')
            # re trigger interrupt
            self.daily_email_int() 
        else:
            self.reTimer(10000,"send_mail_monthly")  #if GO flag on then wait out   
            logging.info('pre_sendmail_monthly - waitout')


    def pre_sendmail_weekly(self):   # evey 7 day 1234567 1 monday 0001 start
        if(self.FLAG_REC==GO):
            
            print Fore.YELLOW + 'pre_sendmail_weekly'
            # get the total data of last 7 days
            self.computation(FILE_DAY_WEEKLY,7) 
            # prepare message block
            mailMsg=self.mail_MsgBlk(self.T_DAY_LITRE, self.T_DAY_COST,7)   
            # transfer to temp file
            self.trFileWeek(FILE_DAY_WEEKLY,"t"+FILE_DAY_WEEKLY)
            # attach weekly file to mail
            self.upiemail.setup_mail2(mailMsg,"Weekly Water Usage","t"+FILE_DAY_WEEKLY)   
            # achived purpose
            self.saveFile("a"+self.timeStamp("T2")+FILE_WEEKLY, str(self.T_DAY_LITRE)+","+str(self.T_DAY_COST)) 
            # clear away the file 
            self.clearFile("t"+FILE_DAY_WEEKLY) 
            logging.info('pre_sendmail_weekly - done')
            # re trigger interrupt
            self.daily_email_int() 

        else:
            self.reTimer(10000,"send_mail_week")     # wait out       
            logging.info('pre send weekly - wait out')

    def pre_sendmail_daily(self):    

        if(self.FLAG_REC==GO):
            self.computation(FILE_HOURLY,1)

            strLitre=str(self.T_DAY_LITRE)     # cast to string 
            strCost=str(self.T_DAY_COST)

            print Fore.RED + 'pre_sendmail_daily'
             # prepare message block
            mailMsg=self.mail_MsgBlk(self.T_DAY_LITRE, self.T_DAY_COST,1) 

            self.trFileDaily(FILE_HOURLY ,"t"+FILE_HOURLY)
            # Save to monthly data, daliy basis
            self.saveFile(FILE_DAY_MONTHLY ,strLitre +","+ strCost)  
             # Save to weekly data, daily basis
            self.saveFile(FILE_DAY_WEEKLY ,strLitre +","+ strCost)   
            
            # attach weekly file to mail
            self.upiemail.setup_mail2(mailMsg,"Daily Water Usage","t"+FILE_HOURLY)
              # achive purpose
            self.saveFile("a"+self.timeStamp("DATESTAMP")+FILE_HOURLY,strLitre +","+ strCost)
           # reset current hourly file 
            self.clearFile(FILE_HOURLY)  
            self.clearFile("t"+FILE_HOURLY)

            logging.info('pre_sendmail_daily - done')
            # re trigger interrupt
            self.daily_email_int()  

        else:
            self.reTimer(10000,"send_mail_daily")
            logging.info('pre_sendmail_daily - waitout')

#---------------------------------------
#  prepare message block for email
#---------------------------------------------

    def mail_MsgBlk(self,litre,cost,mode):    # input in integer
        strLitre=str(litre)     # cast to string 
        strCost=str(cost)

        # -----------------------------------------------
        #Preparing the message for mail : using gobal variable set data rec as string 
        dataRec= "<b>Litre Used (L) :</b> " + strLitre +"<br>"
        dataRec+=" \n<b>Total Cost      :</b> $"+ strCost

        if( mode==1):   # daily  mail
           
           mail_msg=  MAIL_DAILY +"<br><br>"+self.timeStamp("T2")+"\n\n<br><br>"+ dataRec
           logging.debug(MAIL_DAILY + dataRec)
        elif(mode==7):    # weekly mail 
            
           d7=self.timeStamp("d7")  # get the last 7days date
           d1=self.timeStamp("d1")  # get the yesterday date
           mail_msg=MAIL_WEEKLY + "<br><br> Your water usage between <i>" 
           mail_msg+= d7 +"</i> to<i> "+ d1 +"</i>\n\n<br><br>"+ dataRec
           logging.debug(MAIL_WEEKLY + dataRec)
        elif(mode==30):
           mail_msg=  MAIL_MONTHLY +"<br><br>"+self.timeStamp("T2")+"\n\n<br><br>"+ dataRec
           logging.debug(MAIL_MONTHLY + dataRec)


        mail_msg+="<br><br>"+THANKYOU +"<br><br>"+ QOUTE
        return mail_msg
            # -----------------------------------------------



#---------------------------------------------------------
# FUNCTION : PREPARE OF MSG TO BE WRITE
#   saveFile ( filename,"string" )
#   example:  self.saveFile("a"+self.timeStamp("DATESTAMP")+FILE_HOURLY,strLitre +","+ strCost) 
#---------------------------------------------------------
    def saveFile(self,zfile,litre_cost):    
        if (self.FLAG_REC==GO):
           logging.info('saveFile file name :' + zfile)
           rec_msg=""     
           localtime   = time.localtime()
           #example of the fomat output 16,04,2016,Saturday,16:59:03:,0.3,cost
           rec_msg=time.strftime("%d,%m,%Y,%A,%H:%M:%S")
           rec_msg+="," + litre_cost + "\n" 
           
           logging.debug('saveFile - msg:' + rec_msg)
           self.writeFile(zfile,rec_msg)    # write to file 
        else:
           self.reTimer(10001,"save_rec")  # recheck again 08may 2016
           logging.info('save file- wait out')
   
    def reset_costUsage(self):
        #--- clear all data
        self.var_litre.set(str(0.0))
        self.var_cost.set(str(0.00)) 
        self.litre=0.0

    def save_record_hourly(self):    # save water cost in hourly basis
        if (self.FLAG_REC==GO):
           #print "save"
           rec_msg=""     

           localtime = time.localtime()
           #example of the fomat output 16,04,2016,Saturday,16:59:03:,0.3,cost
           rec_msg=time.strftime("%d,%m,%Y,%A,%H:%M:%S")
           rec_msg+="," + str(self.var_litre.get()) +","+(str(self.var_cost.get()))
           rec_msg+="\n"  
           logging.info('save_record_hourly - msg:' + rec_msg)
           self.writeFile(FILE_HOURLY,rec_msg)  # write to hourly file 
           self.reset_costUsage()               # reset the cost usage       
           self.rec_hourly_int()                # restart timer again 
        else:
           self.reTimer(10001,"save_rec")  # recheck after 10 second
           logging.info('save_record_hourly hourly - wait out')
#---------------------------------------------------------
# FUNCTION : FILE READ/WRITE
#---------------------------------------------------------

    def writeFile(self,z_file,msg):
       fo=open(z_file,"a+")  
       line = fo.write( msg )
       fo.close()

    def trFileMth(self,frFile,toFile):
     # Get the last month in string  and read the file 
     # only the last month of record is pass to a new file 
      dM = date.today() + relativedelta(months=-1)  # able to sub date return 2016-03-30 format    
      strCnt=str(dM.month)
      if (len(strCnt)==1):    # if the DM =1,2, 3 it add prefix '0' a 01 , 02, 
       dM2="0" + str(dM.month) 

      f = open(frFile,'r+')
      f1 = open(toFile, 'a+')
      f1.writelines(CSV_HEADER)
      for line in f.readlines():
          posOne=0                      
          posTwo=0                       
          posOne=line.find(",", posOne)     
          posTwo=posOne+1
          posTwo=line.find(",", posTwo)
          mL=line[posOne+1:posTwo]                # get month value
          if str(dM.month) in mL: f1.write(line)  # compare month value (02 or 2) 
          elif str(dM2) in mL: f1.write(line)
      f1.close()

    def trFileWeek(self,frFile,toFile):
     # Purpose: to transfer file to another with specific pervious 7 days record information   
     #
      
      wkarray=["","","","","","","",""]
      wkarray=self.lastWkDate()            # get last 7 date from today's date
      
      f = open(frFile,'r+')                # Read from file...
      f1 = open(toFile, 'a+')              # ...append to other file

      f1.writelines(CSV_HEADER)            # Insert header for .csv
      for line in f.readlines():
          posOne=0    
          posOne=line.find(",", posOne)    # find only what is before the first ','  
          dl=line[:posOne]                 # slice off and get the date value
          for n in range (1,8):            # compare with past 7 days only
           if (str(wkarray[n].day) == dl): f1.write(line)   # transfer  record information

      f1.close()
      f.close()
    def trFileDaily(self, frFile,toFile):
     # Purpose: to transfer file to another with specific pervious 1 days record information   
        f = open(frFile,'r+')
        f1 = open(toFile, 'a+')
        f1.writelines(CSV_HEADER) 

        d1 = date.today() - timedelta(days=1)  # Get previous date
        for line in f.readlines():
          posOne=0                      
          posOne=line.find(",", posOne)    # find only what is before first ','  
          dl=line[:posOne]                 # get date  value 

          if str(d1.day)==dl: f1.write(line) # only the previous day is transfer

        f1.close()
        f.close()

    def clearFile(self,z_file):    # to clear the text file
       f=open(z_file, 'w')
       f.close()
#---------------------------------------------------------
# FUNCTION : COMPUTATION
#---------------------------------------------------------
    def computation(self,rfile,computeMode):
      logging.info('computation mode '+ str(computeMode))
      waterRec=[0,0,0,0,0,0,0]       # 7 water data array
     
      if(computeMode==7):            # before the read file loop, find last 7 days
        wkarray=["","","","","","","",""]
        wkarray=self.lastWkDate()
     # reset gobal data
      self.T_DAY_COST=0.0
      self.T_DAY_LITRE=0.0
      self.T_MOM_COST=0.0
      self.T_MOM_LITRE=0.0

      file=open(rfile,'r').read().splitlines()   # open respective file daily or weekly or monthly
      for line in file :                   # till end of line 
          rl=line
          posA=0
          posB=0
          for num in range(0,7):           # 7 array variable  [ary0,ary1,ary2,ary3,ary4,ary5,ary6]
              posB=rl.find(",",posB+1)     # find the postion of "," 1st
              waterRec[num]=rl[posA:posB]  # load the date, month, year, day, time,litre,cost 
              posA=posB+1                  # swap position
          toDayDate=self.timeStamp("DATE")
          if(computeMode==30):  # for 30 day   1st day of the month
             
             dmth = date.today() + relativedelta(months=-1)  # able to sub date return 2016-03-30 format
             dM="0" + str(dmth.month)   # append "0" to month to form "02" month str
             if dM == waterRec[1] :       # only month match is add
                 self.T_MOM_LITRE+=float(waterRec[5])  # 
                 self.T_MOM_COST+=float(waterRec[6])  
              
          elif(computeMode==1):    #  for  pervious day d-1  
            d1 = date.today() - timedelta(days=1)  # able to sub date return 2016-03-30 format
            if(waterRec[0]==str(d1.day)):
               self.T_DAY_LITRE+=float(waterRec[5]) 
               self.T_DAY_COST+=float(waterRec[6])  
          
          elif(computeMode==7):    # for one week 
            self.compute_ForWk(waterRec,wkarray)
          
      #file.close()   # need not to close 
    
    def compute_ForWk(self,waterRec,wkarray): 
        for n in range(1,8):                 # only the past 7 day is compute
          if(waterRec[0]==str(wkarray[n].day)):  
             self.T_DAY_LITRE+=float(waterRec[5]) 
             self.T_DAY_COST+=float(waterRec[6])  
      
#---------------------------------------------------------
# FUNCTION : DATE & TIME
#---------------------------------------------------------
    def timeStamp(self,index):
       localtime   = time.localtime()
       #example of the fomat output 16,04,2016,Saturday,16:59:03:,0.3,cost
       #  %d=16, %-m=4,%Y=2016,%A=Saturday, %H=hour,%M=min, $S=second
       if(index=="TIMESTAMP"):
           ret=time.strftime("%d,%-m,%Y,%A,%H:%M:%S") 
       elif(index=="T2"):
           ret=time.strftime("%d %B %Y %A Time: %H:%M:%S")
       elif(index=="DATE"):
           ret=time.strftime("%d")
       elif(index=="MONTH"):
           ret=time.strftime("%-m")
       elif(index=="DAY"):
           ret=time.strftime("%A")
       elif(index=="CUR_SEC"):
           ret=time.strftime("%S")
       elif(index=="CUR_MIN"):
           ret=time.strftime("%M")
       elif(index=="CUR_HR"):
           ret=time.strftime("%H")
       elif(index=="DATESTAMP"):
           ret=time.strftime("%d-%-m-%Y")
       elif(index=="d7"):
         d7 = date.today() - timedelta(7)        #  get the date of last week( 7days ago)
         logging.info('timeStamp: '+ str(d7)) 
         d7i=d7.strftime('%A')                   # get the day of the week, example Monday to Sunday 
         ret= str (d7) + " " + str(d7i)          # return the date result in this format 2016-04-30 Saturday

       elif(index=="d1"):
         d = date.today() - timedelta(1)         # get yesterday date
         dwd=d.strftime('%A')       
         ret= str (d) + " " + str(dwd)           # return the date result in this format 2016-04-30 Saturday 

       return ret;       # return result 

    def lastWkDate(self):                       # to find last 7 days's date
        retWkDate=["","","","","","","","",""]  # arrray for past one week date ,0 index is today date 
        for n in range (0,8):
           retWkDate[n]=date.today()-timedelta(n)
        return retWkDate                        # return wk array

    def get_offsetSecond(self):
       cur_min=self.timeStamp("CUR_MIN") 
       cur_hr=self.timeStamp("CUR_HR")
       logger.debug("offset time current Hr"+ cur_hr+" Min "+ cur_min)
       
       offsetHr = int(23)-int(cur_hr)            #Take 2359 as  the time of end of day
       offsetMin = int(59)-int(cur_min)          # 23 hr - current hr  and 59 - current min
       offsetMin *=60000                         # multiple the min with msecond 
       offsetHr*=3600000                         # multiple hr with 3600000msec/hr 
       return (offsetHr + offsetMin )            # return the off time in ms
#-------------------------------------------------------
#
#   # set to first day of that month Example 2016-01-01 , 2016-04-01
#-------------------------------------------------------
    def first_day_of_month(self,d): 
       return date(d.year, d.month, 1)
#----------------------------------------------
# get the number of days between two dates
#---------------------------------------------
    def diff_dates(self,date1, date2):
       return abs(date2-date1).days

#-------------------------------------
# Get the number of day of next Monday
# require fn - diff_dates()
#-------------------------------------

    def findNextMonday(self):

       today = datetime.date.today()     # get today date
       nextMon=today + datetime.timedelta(days=-today.weekday(), weeks=1) # get the next monday date
       diff_Day= self.diff_dates(today,nextMon )   # find the differece of days to next monday

       return int(diff_Day)
#----------------------------------------------
# nextMonth 
# to find the number of day to next 1st day of the month
#  require fn () - first_day_of_month()  
#                - diff_dates()
#---------------------------------------------
    def nextMonth(self):
       date_after_month = datetime.date.today()+ relativedelta(months=1) # get next month
                     
       nextMthFirst=self.first_day_of_month(date_after_month) # set to first day of month
       dayToNextMth=self.diff_dates(datetime.date.today(),nextMthFirst)
       logging.debug("Next month " + str(dayToNextMth))
        # return result number of days to next 1st day of month
       return int(dayToNextMth)   

#---------------------------------------------------------
# FUNCTION : TIMER INTERRUPT
#          To trigger the save record by timer in milisecond
#---------------------------------------------------------

    def reTimer(self,time,z_case):
       if(z_case=="save_rec"):
           self._timer = self.after(time,self.save_record_hourly)
       elif (z_case=="send_mail_daily"):
           self._timer = self.after(time,self.pre_sendmail_daily)
       elif (z_case=="FLAG_INT"):
           self._timer = self.after(time,self.interrupt_Flag)
       elif(z_case=="send_mail_week"):
           self._timer = self.after(time,self.pre_sendmail_weekly)
       elif(z_case=="send_mail_monthly"):
           self._timer = self.after(time,self.pre_sendmail_monthly)

    def interrupt_Flag(self):
        if (FLAG_REC==STOP):   # if not stop then set back to GO
          self.FLAG_REC=GO
        else:
         pass     # do nothing 
    def monthly_email_int(self):
       numOfDay=self.nextMonth()   # return number of days to nextmonth 1st 
       offSetTime=self.convertDayTo_ms(numOfDay)  # convert to ms 
       self._timer = self.after(offSetTime,self.pre_sendmail_monthly)  # By day # temp timer 

    def weekly_email_int(self):
       numOfDay=self.findNextMonday()    # get the next day
       offSetTime=self.convertDayTo_ms(numOfDay)
       self._timer = self.after(offSetTime,self.pre_sendmail_weekly)  # By day

    def daily_email_int(self):
       offSetSec=self.get_offsetSecond()    #  where return how many milisecond to reach 23:59 
       offSetSec+= 600000                   # add another 10 min
       self._timer = self.after(8000,self.pre_sendmail_daily)  # By day

    def rec_hourly_int(self):
       curMin=self.timeStamp("CUR_MIN")
       curSec=self.timeStamp("CUR_SEC")
       offSetSec = ((60 - int(curMin) ) * 60  + (60-int(curSec)) )* 1000 
       self._timer = self.after(offSetSec,self.save_record_hourly)  # recbY  next hour
   
    def convertDayTo_ms(self,day):
       return (day*86400*1000)    # per day * no of second 

#---------------------------------------------------------
# EMAIL CLASS 
#---------------------------------------------------------
class Email(object):
   def __init__(self):
     self.Sender=SENDER
     self.Receiver=RECEIVER
     logging.info('email setup object')
     
#---------------------------------------------------------
#  sendmail : create connect and send mail 
#  current it setup using google mail port number
#---------------------------------------------------------
   def sendmail(self,message):
         self.smtpObj = smtplib.SMTP(SMTP_SERVER,SERVER_NO)
         self.smtpObj.starttls()
         self.smtpObj.ehlo()  
         self.smtpObj.login(uPiMail,password)
         self.smtpObj.sendmail(self.Sender, self.Receiver, message.as_string()) 
         self.smtpObj.close()
         logging.info('send mail - done')
   
#---------------------------------------------------------
# setup mail2 is to configure the mail with attach file 
#  - message : is the content  of email
#  - mailSub : subject title of email
#  - attachFile: file to be attached
#          
#---------------------------------------------------------
   def setup_mail2(self,message,mailSub,attachFile):

    msg = MIMEMultipart()
    msg['From'] = self.Sender
    msg['Subject'] = mailSub
    msg['To'] = self.Receiver
    ctype, encoding = mimetypes.guess_type(attachFile)
    if ctype is None or encoding is not None:
        ctype = "application/octet-stream"

    maintype, subtype = ctype.split("/", 1)
    
    fp = open(attachFile)
    attachment = MIMEBase(maintype, subtype)
    attachment.set_payload(fp.read())
    fp.close()
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", "attachment", filename=attachFile)   # attach file to mail
    msg.attach(MIMEText(   message,"html",_charset='UTF-8'))
    msg.attach(attachment)
    self.sendmail(msg)
	
#---------------------------------------------------------
#  Setup simple mail without any additional message
#---------------------------------------------------------
    
   def setup_mail(self):
    
    msg = MIMEMultipart()
    msg['From'] = self.Sender
    msg['Subject'] = "Setup Email Notification"
    msg['To'] = self.Receiver
    msg.attach(MIMEText(MAIL_SETUP, "html" ))
    logging.info('L814 set up mail - done ')
    self.sendmail(msg)

if __name__ == "__main__":
    app = simpleapp_tk(None)
    app.title('Pi Water Usage v1.1.0')
    app.mainloop()

