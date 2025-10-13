

export default function VideoFeed() {

    return (
        <div className="w-full h-full">
            <video 
                src="/cars.mp4" 
                autoPlay
                loop
                muted
                className="w-full h-full object-cover pointer-events-none"
            />

            {/* <img 
                src="/testImg.jpg" 
                alt="Test image"
            /> */}

        </div>
    );
}