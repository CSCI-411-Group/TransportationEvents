
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


--4.a question
SELECT *
FROM Events
WHERE Person = 'p_9031';

--4.b question
SELECT
    L.*,
    N1.NodeID AS FromNodeID, N1.X AS FromNodeX, N1.Y AS FromNodeY,
    N2.NodeID AS ToNodeID, N2.X AS ToNodeX, N2.Y AS ToNodeY
FROM
    Links L
    JOIN
    Nodes N1 ON L.FromNode = N1.NodeID
    JOIN
    Nodes N2 ON L.ToNode = N2.NodeID
WHERE 
    L.LinkID = '7735018_0';

--4.c
SELECT  
    Person, 
    SUM(Distance) AS TotalDistanceWalked 
FROM  
    Events  
WHERE  
    Type = 'travelled' AND  
    Mode = 'walk' 
GROUP BY  
    Person 
ORDER BY  
    TotalDistanceWalked DESC; 


--4.d
WITH
    StartTimes
    AS
    (
        SELECT
            Person,
            Time AS StartTime,
            link,
            actType
        FROM
            Events
        WHERE 
        Type = 'actstart'
    ),

    EndTimes
    AS
    (
        SELECT
            Person,
            Time AS EndTime,
            link,
            actType
        FROM
            Events
        WHERE 
        Type = 'actend'
    )

,
    Duration
    AS
    (
        SELECT
            s.Person,
            e.EndTime - s.StartTime AS ActivityDuration
        FROM
            StartTimes s
            JOIN
            EndTimes e ON s.Person = e.Person AND s.link = e.link AND s.actType = e.actType
        WHERE 
        e.EndTime > s.StartTime
    )

SELECT
    Person,
    AVG(ActivityDuration) AS AverageActivityTime
FROM
    Duration
GROUP BY 
    Person
HAVING 
    AVG(ActivityDuration) IS NOT NULL
ORDER BY 
    AverageActivityTime ASC;


--4.e
SELECT
    Person,
    MIN(Time) AS EarliestDepartureTime
FROM
    Events
WHERE 
    Type = 'departure' AND LegMode = 'car'
GROUP BY 
    Person
ORDER BY 
    EarliestDepartureTime;

--index
CREATE INDEX idx_person ON Events (Person);
CREATE INDEX idx_link ON Events (Link);
