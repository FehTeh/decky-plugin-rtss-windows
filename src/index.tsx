import {
  PanelSection,
  PanelSectionRow,
  SliderField
} from "@decky/ui";
import {
  callable,
  definePlugin,
  toaster,
} from "@decky/api"
import { useState } from "react";
import { FaChartLine } from "react-icons/fa";

const setOSDStatus = callable<[profile: number], boolean>("set_osd_status");

function PerformanceOverlayLevel() {
  const [currentProfile, setCurrentProfile] = useState(0);

  const handleProfileChange = async (value: number) => {
    setCurrentProfile(value);
    try {
      const success = await setOSDStatus(value);
      if (success) {
        const profileNames = ["OFF", "ON"];
        toaster.toast({
          title: "RTSS Overlay",
          body: `Overlay ${profileNames[value]}`
        });
      } else {
        toaster.toast({
          title: "Error",
          body: "Failed to change RTSS overlay"
        });
      }
    } catch (error) {
      toaster.toast({
        title: "Error",
        body: "An error occurred"
      });
    }
  };

  return (
    <PanelSection>
      <PanelSectionRow>
        <SliderField
          label="Performance Overlay Level"
          value={currentProfile}
          min={0}
          max={1}
          step={1}
          onChange={handleProfileChange}
          notchLabels={[
            { notchIndex: 0, label: "OFF" },
            { notchIndex: 1, label: "ON" }
          ]}
          showValue={false}
        />
      </PanelSectionRow>
    </PanelSection>
  );
}

export default definePlugin(() => {
  console.log("RTSS Plugin initializing")

  return {
    name: "RTSS Overlay",
    icon: <FaChartLine />,
    content: <PerformanceOverlayLevel />,
    alreadyDecorated: true,
  };
});
