drop table events; 
drop table links; 
drop table nodes; 

CREATE TABLE Nodes
(
    ID int PRIMARY KEY,
    NodeID VARCHAR(20) NOT NULL,
    X DECIMAL(30, 15) NOT NULL,
    Y DECIMAL(30, 15) NOT NULL

);


CREATE TABLE Links
(
    ID int PRIMARY KEY,
    LinkID VARCHAR(20) NOT NULL,

    FromNode int NOT NULL,

    ToNode int NOT NULL,

    Length DECIMAL(30, 20) NOT NULL,

    FreeSpeed DECIMAL(30, 20) NOT NULL,

    Capacity INT NOT NULL,

    PermLanes INT NOT NULL,

    OneWay INT NOT NULL,

    Mode VARCHAR(10) NOT NULL,
    -- Usually just car 

    FOREIGN KEY (FromNode) REFERENCES Nodes(ID),

    FOREIGN KEY (ToNode) REFERENCES Nodes(ID)

);

CREATE TABLE Events
(
    EventID serial PRIMARY KEY,

    Time NUMERIC(20, 1) NOT NULL,

    Type TEXT NOT NULL,

    LinkID int,

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

    LegMode VARCHAR(20)

    -- FOREIGN KEY (LinkID) REFERENCES Links(ID)

);

--index
CREATE INDEX idx_person ON Events (Person);
CREATE INDEX idx_link ON Events (Link);
