/* PC1 side UDP Tx implementation */

#include <stdio.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <string.h>
#include <fcntl.h>
#include <stdlib.h>
#include <sys/time.h>
#include <stdbool.h>
#include <stdarg.h>
#include <pthread.h>
#include "coopMsg.h"

#define HOSTNAME "192.168.1.6"
#define PORT     4200
#define DEBUG_LV 2
#define BUF_SIZE 1024


typedef enum{
  DEBUG_MSG_LV_NONE = 0,
  DEBUG_MSG_LV_LOW = 1,
  DEBUG_MSG_LV_MID = 2,
  DEBUG_MSG_LV_HIGH = 3
}DEBUG_MSG_LV;

struct sockaddr_in servaddr;
static int fd = -1;


static pthread_t pCmdThread;
static bool testMenuPrintStatus = true;
static int choiceNum = -1;
static bool state = true;

static char *__bar ="---------------------------------------------------------------";

char t_buf[BUF_SIZE];

const char* getDateTimeStr(void)
{
	static char buf[32];
	struct timeval tv;
	struct tm *ptm;
	int    Y, M, D, h, m, s, mcs;

	gettimeofday(&tv, NULL);
	ptm = localtime(&tv.tv_sec);

	Y   = ptm->tm_year + 1900;
	M   = ptm->tm_mon + 1;
	D   = ptm->tm_mday;
	h   = ptm->tm_hour;
	m   = ptm->tm_min;
	s   = ptm->tm_sec;
	mcs = tv.tv_usec;

	sprintf(buf, "%04d-%02d-%02d.%02d:%02d:%02d.%06d",Y,M,D,h,m,s,mcs);

	return buf;
}


void Test_Msg_Print(char* format, ...)
{
	va_list arg;
	printf("\n#### V2X Message: ");
	va_start(arg, format);
	vprintf(format,arg);
	va_end( arg);

    {
        char szBuf[1024] = {0, };

        va_list lpStart;
        va_start(lpStart, format);
        vsprintf(szBuf, format, lpStart);
        va_end(lpStart);    
    }
}


void Debug_Msg_Print(int msgLv, char* format, ...)
{
	va_list arg;

    if(msgLv <= DEBUG_LV )
	{
		printf("$ [DT=%s] - DEBUG[%d]: ", getDateTimeStr(), msgLv);

		va_start(arg, format);
		vprintf(format,arg);
		va_end( arg);		
		
		printf("\n");

		{
			char szBuf[1024] = {0, };
            
			va_list lpStart;
			va_start(lpStart, format);
			vsprintf(szBuf, format, lpStart);
			va_end(lpStart);
		}
	}
}

void Debug_Msg_Print_Data(int msgLv, unsigned char* data, int len)
{
    int rep;
    if(msgLv <= DEBUG_LV)
    {
		printf("\n\t (Len : 0x%X(%d) bytes)", len, len);
		printf("\n\t========================================================");
		printf("\n\t Hex.   00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F");
		printf("\n\t--------------------------------------------------------");
		for(rep = 0 ; rep < len ; rep++)
		{
			if(rep % 16 == 0) printf("\n\t %03X- : ", rep/16);
			printf("%02X ", data[rep]);
		}
		printf("\n\t========================================================");
		printf("\n\n");
    }
}


bool Test_App_Main(void)
{
	bool rtnVal = true;
	int re = 0;
	choiceNum = -1;
	memset(t_buf,0, sizeof(t_buf));	

	printf("\n%s", __bar);

	if (testMenuPrintStatus == true)
	{
		Test_Msg_Print("Please select menu ");
		Test_Msg_Print("< V2X Message Set >-------------------");
		Test_Msg_Print("[1] BSM");
		Test_Msg_Print("[2] PIM");
		Test_Msg_Print("[3] DMM");
		Test_Msg_Print("[4] DNM_Request");
		Test_Msg_Print("[5] DNM_Response");
		Test_Msg_Print("[6] DNM_Done");
		Test_Msg_Print("[7] EDM");

		Test_Msg_Print("< EXIT >-------------------------------");
		Test_Msg_Print("[0] Exit");
	}
	Test_Msg_Print("Enter your choice : \n");

	re = scanf("%d", &choiceNum);
	printf("\n%s", __bar);
	Test_Msg_Print("choiceTest Number: %d\n\n", choiceNum);

	if ((choiceNum > 7) || (choiceNum < 0))
		return false;


	DMM_EDM *t_msg;
	DNM *t_msg4;
	PIM *t_msg2;
        Msg_Header *t_head;
	int rand_m= 0;

	switch (choiceNum)
	{
	case 0:
		rtnVal = false;
		break;
	case 1:
		t_head = (Msg_Header *)t_buf;
		t_head->MsgType = 1;
		t_head->PacketLen = sizeof(Msg_Header); 
		Debug_Msg_Print_Data(DEBUG_MSG_LV_MID, t_buf, t_head->PacketLen );			
		break;

	case 2:
		Debug_Msg_Print(DEBUG_MSG_LV_LOW," >> PIM len: %d",(int) sizeof(PIM));
		t_msg2 =(PIM *)t_buf;

		t_msg2->header.MsgType = 2;
		t_msg2->header.PacketLen = sizeof(PIM);

		break;

	case 3:
		Debug_Msg_Print(DEBUG_MSG_LV_LOW," >> DMM len: %d",(int) sizeof(DMM_EDM));
		t_msg =(DMM_EDM *)t_buf;

		t_msg->header.MsgType = 3;
		t_msg->header.PacketLen = sizeof(DMM_EDM);

		rand_m = rand();
		rand_m = (rand_m % 8) + 1;
		t_msg->ManeuverType = rand_m; 
		t_msg->RemainDistance = rand();

		switch(t_msg->ManeuverType)
		{
			case 1: Debug_Msg_Print(DEBUG_MSG_LV_LOW,"  %dm Straight Driving", t_msg->RemainDistance);
			break;
			case 2: Debug_Msg_Print(DEBUG_MSG_LV_LOW,"  %dm Lane Change - Left", t_msg->RemainDistance);
			break;
			case 3: Debug_Msg_Print(DEBUG_MSG_LV_MID,"  %dm Lane Change - Right", t_msg->RemainDistance);
			break;
			case 4: Debug_Msg_Print(DEBUG_MSG_LV_LOW,"  %dm Intersection - Straight", t_msg->RemainDistance);
			break;
			case 5: Debug_Msg_Print(DEBUG_MSG_LV_LOW,"  %dm Intersection - Left", t_msg->RemainDistance);
			break;
			case 6: Debug_Msg_Print(DEBUG_MSG_LV_LOW,"  %dm Intersection - Right", t_msg->RemainDistance);
			break;
			case 7: Debug_Msg_Print(DEBUG_MSG_LV_LOW,"  %dm U-Turn", t_msg->RemainDistance);
			break;
			case 8: Debug_Msg_Print(DEBUG_MSG_LV_LOW,"  %dm Overtaking", t_msg->RemainDistance);
			break;
			default: Debug_Msg_Print(DEBUG_MSG_LV_LOW,"  NO define Maneuver");
			break;
		}

		Debug_Msg_Print_Data(DEBUG_MSG_LV_MID, t_buf, t_msg->header.PacketLen );			
		break;

	case 4:
		Debug_Msg_Print(DEBUG_MSG_LV_LOW," >> DNM Req len: %d",(int) sizeof(DNM));

		t_msg4 =(DNM *)t_buf;
		t_msg4->header.MsgType = 4;
		t_msg4->header.PacketLen = sizeof(DNM);

		t_msg4->Sender = 6; //IP D Class
		t_msg4->Receiver = 5;
		t_msg4->AgreeFlag = 1;//Default
		t_msg4->NegoDone = 0; //Default
		Debug_Msg_Print_Data(DEBUG_MSG_LV_MID, t_buf, t_msg4->header.PacketLen );
		break;
	case 5:
		Debug_Msg_Print(DEBUG_MSG_LV_LOW," >> DMM Res len: %d",(int) sizeof(DNM));
		t_msg4 =(DNM *)t_buf;
		t_msg4->header.MsgType = 5;
		t_msg4->header.PacketLen = sizeof(DNM);
		t_msg4->Sender = 5;
		t_msg4->Receiver = 6;
		t_msg4->AgreeFlag = 1;//Default - Agreement 1
		t_msg4->NegoDone = 1; //Default 0, Negotiation 1
		Debug_Msg_Print_Data(DEBUG_MSG_LV_MID, t_buf, t_msg4->header.PacketLen );
		break;
	case 6:
		Debug_Msg_Print(DEBUG_MSG_LV_LOW," >> DMM Don len: %d",(int) sizeof(DNM));
		t_msg4 =(DNM *)t_buf;
		t_msg4->header.MsgType = 6;
		t_msg4->header.PacketLen = sizeof(DNM);
		t_msg4->Sender = 6;
		t_msg4->Receiver = 5;
		t_msg4->AgreeFlag = 1;//Default - Agreement 1
		t_msg4->NegoDone = 2; // Done 2
		Debug_Msg_Print_Data(DEBUG_MSG_LV_MID, t_buf, t_msg4->header.PacketLen );
		break;
	case 7:
		Debug_Msg_Print(DEBUG_MSG_LV_LOW," >> EDM len: %d",(int) sizeof(DMM_EDM));
		t_msg =(DMM_EDM *)t_buf;

		t_msg->header.MsgType = 7;
		t_msg->header.PacketLen = sizeof(DMM_EDM);

		rand_m = rand();
		rand_m = (rand_m % 8) + 1;
		t_msg->ManeuverType = rand_m; 
		t_msg->RemainDistance = rand();

		switch(t_msg->ManeuverType)
		{
			case 1: Debug_Msg_Print(DEBUG_MSG_LV_LOW,"  %dm Straight Driving", t_msg->RemainDistance);
			break;
			case 2: Debug_Msg_Print(DEBUG_MSG_LV_LOW,"  %dm Lane Change - Left", t_msg->RemainDistance);
			break;
			case 3: Debug_Msg_Print(DEBUG_MSG_LV_MID,"  %dm Lane Change - Right", t_msg->RemainDistance);
			break;
			case 4: Debug_Msg_Print(DEBUG_MSG_LV_LOW,"  %dm Intersection - Straight", t_msg->RemainDistance);
			break;
			case 5: Debug_Msg_Print(DEBUG_MSG_LV_LOW,"  %dm Intersection - Left", t_msg->RemainDistance);
			break;
			case 6: Debug_Msg_Print(DEBUG_MSG_LV_LOW,"  %dm Intersection - Right", t_msg->RemainDistance);
			break;
			case 7: Debug_Msg_Print(DEBUG_MSG_LV_LOW,"  %dm U-Turn", t_msg->RemainDistance);
			break;
			case 8: Debug_Msg_Print(DEBUG_MSG_LV_LOW,"  %dm Overtaking", t_msg->RemainDistance);
			break;

			default: Debug_Msg_Print(DEBUG_MSG_LV_LOW,"  NO define Maneuver");
			break;
		}

		Debug_Msg_Print_Data(DEBUG_MSG_LV_MID, t_buf, t_msg->header.PacketLen );			
		break;

	default:
		Debug_Msg_Print(DEBUG_MSG_LV_LOW, "\tIt was the wrong choice !");
		break;
	} /*End of switch*/
	
	int s_size = t_buf[2];

	if(s_size > 0){
		
		if ( write(fd, t_buf, s_size) < 0)
	    	{
			perror("cannot send message");
			close(fd);
			return 0;
		}
		else 
			Debug_Msg_Print(DEBUG_MSG_LV_LOW, "Send V2X Message SET through port %d", PORT);
	} 
	return rtnVal;

}

void* Cmd_thread_func(void *data)
{
	memset(t_buf,0, sizeof(t_buf));	
   //for first connection from client to server
	Debug_Msg_Print(DEBUG_MSG_LV_LOW, "Init Message to server");
	Debug_Msg_Print_Data(DEBUG_MSG_LV_MID, t_buf, sizeof(Msg_Header) );			
		
	if (write(fd, t_buf, sizeof(Msg_Header)) < 0)
    	{
		perror("cannot send message");
		//close(fd);
		//return 0;
	}

	while (state)
	{
		/* Test Application call*/
		if (Test_App_Main() == false)
		{
			state = false;
			return 0;
		}

		usleep(5000);
	}
}


int main(void)
{
    char msg[BUF_SIZE];
    memset(msg, 0, sizeof(msg));
  
    fd = socket(AF_INET,SOCK_DGRAM,IPPROTO_UDP);

    if(fd < 0){
        perror("cannot open socket");
        return 0;
    }else 
	Debug_Msg_Print(DEBUG_MSG_LV_LOW, "open socket");

    bzero(&servaddr,sizeof(servaddr));
    servaddr.sin_family = AF_INET;
    servaddr.sin_addr.s_addr = inet_addr(HOSTNAME);
    servaddr.sin_port = htons(PORT);
    
    int opt_val = 1;
   
    connect(fd, (struct sockaddr*) &servaddr, sizeof(servaddr));
    Debug_Msg_Print(DEBUG_MSG_LV_LOW, "server connect port, %d",PORT);

  //  if (sendto(fd, msg, strlen(msg)+1, 0, // +1 to include terminator
  //             (struct sockaddr*)&servaddr, sizeof(servaddr)) < 0){
  /*  if ( write(fd, msg, strlen(msg)) < 0)
    {
        perror("cannot send message");
        close(fd);
        return 0;
    }
    else printf("send Hello one through port %d\n", servaddr.sin_port);
    
   */
    int len, n;

   struct timeval t_val={10, 0}; //sec, msec
   //SO_RCVTIMEP = 20
    setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &t_val, sizeof(t_val));

    int status = 0;
    int thr_rc = 0;
    int a = 1;

    thr_rc = pthread_create(&pCmdThread, NULL, Cmd_thread_func, (void *)&a);
    if (thr_rc < 0)
    {
		perror("cmd thread create error : ");
		exit(0);
    }

    while(state)
    {
      	//n = recvfrom(fd, (char*)msg, 10, 0, (struct sockaddr *)&servaddr, &len);
		n = read(fd, msg, BUF_SIZE);
		if(n > 0) {
			Debug_Msg_Print(DEBUG_MSG_LV_LOW, "\n\nread() ===> UDP read n = %d", n);
        }
			
	usleep(5000);
    }
    
    pthread_join(pCmdThread, (void **)&status);
    Debug_Msg_Print(DEBUG_MSG_LV_LOW, "ByeBye");

    close(fd);
    return 0;
}
