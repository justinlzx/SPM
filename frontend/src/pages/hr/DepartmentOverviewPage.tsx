import React, { useEffect, useState, useContext } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { UserContext } from "../../context/UserContextProvider";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

type TWFHRequest = {
  // Define the properties of TWFHRequest based on your requirements
};

type TFilter = {
  status: string;
  department: string;
  date: string;
};

const DepartmentOverviewPage = () => {
  const navigate = useNavigate();
  const { user } = useContext(UserContext);

  useEffect(() => {
    if (!user) {
      navigate("/login");
    }
  }, [user, navigate]);

  useEffect(() => {
    const getWFHRequests = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/arrangements`);
        console.log(response.data);
      } catch (error) {
        console.error(error);
      }
    };
    getWFHRequests();
  }, []);

  const [data, setData] = useState<TWFHRequest[]>([]);
  const [filters, setFilters] = useState<TFilter>({
    status: "approved",
    department: "",
    date: "",
  });

  return <div>{/* Your component JSX goes here */}</div>;
};

export default DepartmentOverviewPage;
