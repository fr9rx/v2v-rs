use libm::roundf;
use postcard::experimental::max_size::MaxSize;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Copy, Clone, MaxSize)]
pub struct PositionMessage {
    pub car_id: u16,
    pub packet_id: u16,
    pub latitude: i32,
    pub altitiude: i16,
    pub heading: u8,
    pub longitude: i32,
    pub speed: u8,
}

impl PositionMessage {
    pub fn new(
        id: u16,
        latitiude: f32,
        longitude: f32,
        heading_deg: f32,
        speed: f32,
        altitude: f32,
        packet_id: u16,
    ) -> PositionMessage {
        PositionMessage {
            car_id: id,
            latitude: (latitiude * 1e7) as i32,
            altitiude: roundf(altitude) as i16,
            heading: roundf(heading_deg * (255.0 / 360.0)) as u8,
            longitude: (longitude * 1e7) as i32,
            speed: roundf(speed) as u8,
            packet_id: packet_id,
        }
    }
}

#[derive(Serialize, Deserialize, Debug, Copy, Clone, MaxSize)]
pub enum Message {
    Position(PositionMessage),
}
