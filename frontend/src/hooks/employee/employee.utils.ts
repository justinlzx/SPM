import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export type TEmployee = {
  requester_staff_id: number;
  staff_fname: string;
  staff_lname: string;
  requester_name?: string; // Add requester_name to the type
  position: string;
  country: string;
  email: string;
  dept: string;
  reporting_manager?: number;
  role: number;
};

export const fetchEmployeeByStaffId = async (staffId: number): Promise<TEmployee | null> => {
  try {
    const response = await axios.get(`${BACKEND_URL}/employees/${staffId}`);
    const data = response.data;
    const requester_name = `${data.staff_fname} ${data.staff_lname}`;
    console.log(requester_name);
    return {
      ...data,
      requester_name, 
    };
  } catch (error) {
    console.error(`Failed to fetch employee by staff ID: ${staffId}`, error);
    return null;
  }
};

// Fetch employee by email
export const fetchEmployeeByEmail = async (email: string): Promise<TEmployee | null> => {
  try {
    const response = await axios.get(`${BACKEND_URL}/employees/email/${email}`);
    return response.data;
  } catch (error) {
    console.error(`Failed to fetch employee by email: ${email}`, error);
    return null;
  }
};