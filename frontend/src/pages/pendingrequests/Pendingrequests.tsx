// export const PendingRequests = () => {

//   return (
//     <div>
//       Pending Requests 
      
//     </div>
//   );
// };


import React, { useEffect, useState } from "react";
import axios from "axios";

// Define the type for employees
type Employee = {
  employee_id: number;
  first_name: string;
  last_name: string;
  department: string;
};

const EmployeeList = () => {
  const [employees, setEmployees] = useState<Employee[]>([]);

  useEffect(() => {
    const fetchEmployees = async () => {
      try {
        const response = await axios.get("./backend/src/arrangements/crud.py");  // Call the API
        setEmployees(response.data);  // Set employees data
      } catch (error) {
        console.error("Error fetching employees:", error);
      }
    };

    fetchEmployees();  // Fetch employees when component mounts
  }, []);

  return (
    <div>
      <h2>Employee List</h2>
      <table>
        <thead>
          <tr>
            <th>Employee ID</th>
            <th>First Name</th>
            <th>Last Name</th>
            <th>Department</th>
          </tr>
        </thead>
        <tbody>
          {employees.map((employee) => (
            <tr key={employee.employee_id}>
              <td>{employee.employee_id}</td>
              <td>{employee.first_name}</td>
              <td>{employee.last_name}</td>
              <td>{employee.department}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default EmployeeList;