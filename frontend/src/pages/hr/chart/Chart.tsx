import { Pie } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";
import { ChartOptions } from "chart.js";
import Box from "@mui/material/Box/Box";

// Register the necessary Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend);

export const Chart = ({
  data,
  labels,
  backgroundColor,
  hoverBackgroundColor,
}: {
  data: number[];
  labels: string[];
  backgroundColor: string[];
  hoverBackgroundColor: string[];
}) => {
  const dataConfig = {
    labels,
    datasets: [
      {
        label: "Organisation Chart",
        data: data,
        backgroundColor,
        hoverBackgroundColor,
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

  return (
    <Box className="flex justify-center">
      <Pie data={dataConfig} options={options} />
    </Box>
  );
};
