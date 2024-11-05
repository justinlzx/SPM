import { Pie } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";
import { ChartOptions } from "chart.js";

// Register the necessary Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend);

export const Chart = ({ data }: { data: number[] }) => {
  const dataConfig = {
    labels: ["On Leave", "In Office", "WFH(Full Day)", "WFH(AM)", "WFH(PM)"],
    datasets: [
      {
        label: "Organisation Chart",
        data: data,
        backgroundColor: [
          "#FF6384",
          "#36A2EB",
          "#FFCE56",
          "#FF6384",
          "#36A2EB",
        ],
        hoverBackgroundColor: [
          "#FF6384",
          "#36A2EB",
          "#FFCE56",
          "#FF6384",
          "#36A2EB",
        ],
      },
    ],
  };

  const options: ChartOptions<"pie"> = {
    responsive: true,
    plugins: {
      legend: {
        position: "top",
      },
      tooltip: {
        enabled: true,
      },
    },
  };

  return <Pie data={dataConfig} options={options} />;
};
