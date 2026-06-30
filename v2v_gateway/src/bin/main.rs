#![no_std]
#![no_main]

use embassy_executor::Spawner;
use esp_alloc::export::enumset::EnumSet;
use esp_backtrace as _;
use esp_hal::clock::CpuClock;
use esp_hal::timer::timg::TimerGroup;
use esp_hal::usb_serial_jtag::UsbSerialJtag;
use esp_println::println;
use esp_radio::esp_now::WifiPhyRate;
use esp_radio::wifi::{Protocol, Protocols};
use postcard::from_bytes;
use v2v_sniffer::{HostMessage, Message};

extern crate alloc;
esp_bootloader_esp_idf::esp_app_desc!();

#[esp_rtos::main]
async fn main(_spawner: Spawner) {
    let dp = esp_hal::init(esp_hal::Config::default().with_cpu_clock(CpuClock::max()));
    esp_alloc::heap_allocator!(size: 60 * 1024);

    let timg0 = TimerGroup::new(dp.TIMG0);
    let sw_interrupt = esp_hal::interrupt::software::SoftwareInterruptControl::new(dp.SW_INTERRUPT);
    esp_rtos::start(timg0.timer0, sw_interrupt.software_interrupt0);

    let (mut controller, interfaces) =
        esp_radio::wifi::new(dp.WIFI, Default::default()).expect("WiFi init failed");

    let mut lr_protocol_enumset = EnumSet::new();
    lr_protocol_enumset.insert(Protocol::LR);
    let lr_protocol = Protocols::default().with_2_4(lr_protocol_enumset);
    controller
        .set_protocols(lr_protocol)
        .expect("Failed to set LR protocol");

    let (manger, _sender, mut receiver) = interfaces.esp_now.split();

    if let Err(e) = manger.set_channel(13) {
        println!("set_channel failed: {:?}", e);
    }
    if let Err(e) = manger.set_rate(WifiPhyRate::RateLora250k) {
        println!("set_rate failed: {:?}", e);
    }

    let peer_count = manger
        .peer_count()
        .map(|pc| pc.total_count)
        .unwrap_or_else(|e| {
            println!("peer_count failed: {:?}", e);
            0
        });
    println!("Peer Count: {}", peer_count);

    let (_rx, mut tx) = UsbSerialJtag::new(dp.USB_DEVICE).into_async().split();

    loop {
        let capactured_packet = receiver.receive_async().await;
        let deserialized_message: Message = from_bytes(capactured_packet.data()).unwrap();
        match deserialized_message {
            Message::Position(data) => {
                let host_message = HostMessage {
                    car_id: data.car_id,
                    packet_id: data.packet_id,
                    latitude: data.latitude,
                    longitude: data.longitude,
                    altitude: data.altitiude,
                    speed: data.speed,
                    heading: data.heading,
                };
                let mut buffer = [0 as u8; 50];
                minicbor::encode(&host_message, buffer.as_mut()).unwrap();
                let length = minicbor::len(&host_message);
                tx.write(&buffer[..length]);
                tx.flush_tx();
            }
        }
    }
}
