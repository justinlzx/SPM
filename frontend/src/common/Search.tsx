import React, { useState, useEffect } from "react";
import { TextField } from "@mui/material";

interface SearchProps<T extends object> {
data: T[];
onSearchResult: (results: T[]) => void;
}

export const Search = <T extends object>({ data, onSearchResult }: SearchProps<T>) => {
const [searchTerm, setSearchTerm] = useState("");

useEffect(() => {
    const filteredData = data.filter((item) => {
    // Ensure item is an object and use Object.values for filtering
    return Object.values(item as object).some(value => 
        value?.toString().toLowerCase().includes(searchTerm.toLowerCase())
    );
    });
    onSearchResult(filteredData);
}, [searchTerm, data, onSearchResult]);

const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
};



return (
    <TextField
    label="Search"
    variant="outlined"
    fullWidth
    margin="normal"
    value={searchTerm}
    onChange={handleSearch}
    placeholder="Search..."
    />
);
};

export default Search;
