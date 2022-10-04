#ifndef COOPMSG_H
#define COOPMSG_H

//--------------------------------------------------------
// ETRI-V2X
// Update Date : 2022-09-29
// Update Des  : DMM_EDM Add TmpID 
// Description : Create Message structure PIM, DMM, DNM
// Edit by : neuron
//---------------------------------------------------------

typedef struct
{
	unsigned char MsgType;
	unsigned short PacketLen;

} Msg_Header;

typedef struct
{
	unsigned short ObjID;
	unsigned char Classification;	
	float OutBox_x1;
	float OutBox_y1;
	float OutBox_x2;
	float OutBox_y2;
	float OutBox_x3;
	float OutBox_y3;
	float OutBox_x4;
	float OutBox_y4;
	float Velocity_x;
	float Velocity_y;

} ObjectInfo;

typedef enum 
{
	UNAVAILABLE,
	DARK,
	READ,
	GREEN = 4, 
	YELLOW = 7
} Color;

typedef struct
{
	Color TrafficLight;
	unsigned char ExtLight;

} LightInfo;

typedef struct 
{
	Msg_Header header;
	double MapOrigin_x; //double = float type, 8Byte
	double MapOrigin_y;
	float CrntLoc_x;
	float CrntLoc_y;
	float CrntLoc_heading;
	float DestLoc_x;
	float DestLoc_y;
	unsigned short ObjNum;
	unsigned char ObjType;
	float Accuracy;
	ObjectInfo *Obj_i;
	LightInfo  Lig_i;
} PIM;  //Perception Information Message(1)

typedef enum 
{
	STRAIGHT_DRIVE = 1,
	INTERSECTION_STRAIGHT,
	INTERSECTION_LEFT,
	INTERSECTion_RIGHT,
	LANECHANGE_LEFT,
	LANECHANGE_RIGHT,
	U_TURN,
	OVERTAKING
} Maneuver;

typedef struct
{
	Msg_Header header;
	unsigned int Tmpid; // BSM-Temporary Id, Sender Vehicle
	Maneuver ManeuverType;
	unsigned char RemainDistance;

} DMM_EDM; // Driving Maneuver Message(2) & Emergence Driving Message(6)

typedef struct
{
	Msg_Header header;
	unsigned int Sender;	
	unsigned int Receiver;
	unsigned char AgreeFlag; //Agreement 1 (default), disagreement (0)
	unsigned char NegoDone; //Default 0, Negotiation 1, Done 2

} DNM; //Driving Negotiation Message Request(3), Response(4), Ack(5)


ObjectInfo Percepion[10];

#endif //COOPMSG_H
