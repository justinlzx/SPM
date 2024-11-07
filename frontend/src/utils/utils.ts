export const capitalize = (str: string | undefined | null): string  => {
  if (!str) return "";
  return str
    .split(" ") 
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()) // Capitalize first letter of each word
    .join(" "); 
};

export const JACK_SIM_STAFF_ID: number = 130002;