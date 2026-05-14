# Architecture

flowchart TD
    subgraph Vision ["Vision Engine (Python)"]
        Cam[Camera Feed]
        HT[Hand Tracker]
        AP[Hand Analysis Pipeline]
        FE[Feature Extractor]
        GE[Gesture Engine]
        EQ[Event Queue]
        HUD[HUD Renderer]
    end

    subgraph Comm ["Communication Layer"]
        MQTT[MQTT Manager]
    end

    subgraph ESP ["Embedded Simulation (Wokwi)"]
        ESP32[ESP32 DevKit]
        OLED[OLED Controller\nSSD1306]
        Neo[NeoPixel Controller]
        Router[Message Router]
    end

    Cam --> HT
    HT --> FE
    FE --> AP
    AP --> GE
    GE --> EQ
    EQ --> HUD
    EQ --> MQTT
    MQTT <--> ESP32
    ESP32 --> OLED
    ESP32 --> Neo
    ESP32 --> Router

    classDef python fill:#3776AB, color:white
    classDef mqtt fill:#660066, color:white
    classDef embedded fill:#000000, color:white
    
    class Vision python
    class Comm mqtt
    class ESP embedded
