
select *
from nodes
select *
from links
select *
from events


drop table events

SELECT COUNT(*) AS NodeCount
FROM Nodes;
SELECT COUNT(*) AS NodeCount
FROM links;
SELECT COUNT(*) AS NodeCount
FROM events;

CREATE TABLE Nodes
(

    NodeID VARCHAR(20) PRIMARY KEY NOT NULL,

    X DECIMAL(30, 15) NOT NULL,

    Y DECIMAL(30, 15) NOT NULL

);


CREATE TABLE Links
(

    LinkID VARCHAR(20) PRIMARY KEY NOT NULL,

    FromNode VARCHAR(20) NOT NULL,
    -- NodeID in Nodes is (20) 

    ToNode VARCHAR(20) NOT NULL,
    -- NodeID in Nodes is (20) 

    Length DECIMAL(30, 20) NOT NULL,

    FreeSpeed DECIMAL(30, 20) NOT NULL,

    Capacity INT NOT NULL,

    PermLanes INT NOT NULL,

    OneWay INT NOT NULL,

    Mode VARCHAR(10) NOT NULL,
    -- Usually just car 



    FOREIGN KEY (FromNode) REFERENCES Nodes(NodeID),

    FOREIGN KEY (ToNode) REFERENCES Nodes(NodeID)

);

CREATE TABLE Events
(
    EventID serial PRIMARY KEY,

    Time NUMERIC(20, 1) NOT NULL,

    Type TEXT NOT NULL,

    Link VARCHAR(20),
    -- FK to LinkID 

    DepartureID VARCHAR(20),

    DvrpVehicle VARCHAR(20),

    Request VARCHAR(20),

    Purpose TEXT,

    Amount NUMERIC(30, 20),

    DriverID VARCHAR(20),

    TransactionPartner TEXT,

    Vehicle VARCHAR(20),

    Mode VARCHAR(10),

    Delay NUMERIC(20, 1),

    TransitLineID VARCHAR(20),

    AtStop NUMERIC(20,1),

    Person VARCHAR(20),

    Agent VARCHAR(20),

    RelativePosition NUMERIC(5, 4),

    NetworkMode TEXT,

    TaskType TEXT,

    TaskIndex INT,

    DestinationStop VARCHAR(20),

    TransitRouteID VARCHAR(20),

    Distance NUMERIC(30, 20),

    Facility VARCHAR(20),

    X NUMERIC(30, 15),

    Y NUMERIC(30, 15),

    DvrpMode VARCHAR(20),

    VehicleID VARCHAR(20),

    ActType TEXT,

    LegMode VARCHAR(20),



    FOREIGN KEY (Link) REFERENCES Links(LinkID)

); 