import { useState } from "react";
import Button from "@mui/material/Button";

type PropType = {
  action: ({ start, end }: { start: Date; end: Date }) => void;
};

enum DateRange {
  From = "from",
  To = "to",
}

const formatDate = (date: Date) => {
  const year = date.getFullYear();
  const month = date.getMonth() + 1; // Months are zero-based
  const day = date.getDate();

  // Pad month and day with zero if needed
  const monthStr = month < 10 ? "0" + month : month;
  const dayStr = day < 10 ? "0" + day : day;

  return `${year}-${monthStr}-${dayStr}`;
};

export const DatePicker = ({ action }: PropType) => {
  const [dates, setDates] = useState({
    start: new Date(),
    end: new Date(),
  });
  const [error, setError] = useState("");

  const handleDateChange = (value: string, type: string) => {
    const date = new Date(value);
    if (type === DateRange.From) {
      setDates((prev) => ({
        ...prev,
        start: date,
      }));
    } else {
      setDates((prev) => ({
        ...prev,
        end: date,
      }));
    }
  };

  const handleFixedDateSelect = (days: number) => {
    const newEnd = new Date(
      dates.end.getTime() - (days - 1) * 24 * 60 * 60 * 1000
    );
    setDates((prev) => ({
      ...prev,
      end: newEnd,
    }));
  };

  return (
    <div className="p-20">
      <div className="flex flex-col items-center">
        <div className="flex gap-2">
          <button
            className="p-2 px-3 font-leagueSpartan-400 text-orange border border-orange rounded-lg hover:bg-lightOrange"
            onClick={() => handleFixedDateSelect(7)}
          >
            Last 7 days
          </button>
          <button
            className="p-2 px-3 font-leagueSpartan-400 text-orange border border-orange rounded-lg hover:bg-lightOrange"
            onClick={() => handleFixedDateSelect(15)}
          >
            Last 15 days
          </button>
          <button
            className="p-2 px-3 font-leagueSpartan-400 text-orange border border-orange rounded-lg hover:bg-lightOrange"
            onClick={() => handleFixedDateSelect(30)}
          >
            Last 30 days
          </button>
        </div>
        <div className="flex justify-center">
          <div className="flex flex-col gap-2 p-4">
            <label className="mx-1 font-leagueSpartan-400">From</label>
            <input
              type="date"
              className="w-[180px] border border-neutral-300 font-leagueSpartan-400 rounded-lg"
              value={formatDate(dates.start)}
              onChange={(e) => {
                handleDateChange(e.target.value, DateRange.From);
              }}
            />
          </div>
          <div className="flex flex-col gap-2 p-4">
            <label className="mx-1 font-leagueSpartan-400">To</label>
            <input
              type="date"
              className="w-[180px] border border-neutral-300 font-leagueSpartan-400 rounded-lg"
              value={formatDate(dates.end)}
              onChange={(e) => {
                handleDateChange(e.target.value, DateRange.To);
              }}
            />
          </div>
        </div>
        <div className="grid grid-cols-1">
          {error && <p className="text-red-500">{error}</p>}
          <div className="flex justify-center">
            <Button
              sx={{
                backgroundColor: "navy",
                color: "white",
              }}
            >
              Go
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
