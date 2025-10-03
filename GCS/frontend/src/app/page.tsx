import GUI from '../components/HUD/HUD';
import InfoDashBoard from '../components/InfoDashboard/InfoDashBoard';

export default function Home() {
  return (
    <div className="font-sans min-h-screen w-full flex flex-col bg-black">

      <div className="h-[68vh] w-full bg-neutral-900 border-b border-neutral-800">
        <GUI />
      </div>
      
      <div className="h-[32vh] w-full bg-black">
        <InfoDashBoard />
      </div>

    </div>
  );
}
