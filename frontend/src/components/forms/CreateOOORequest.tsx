import React, { useContext, useState } from 'react';
import { UserContext } from '../../context/UserContextProvider';
import { useNavigate } from 'react-router-dom';
import { Formik, Form, Field, ErrorMessage } from 'formik';
import { addDays, isAfter, isWeekend } from 'date-fns';
import { SnackBarComponent, AlertStatus } from '../../common/SnackBar';
import {
  Box,
  Container,
  TextField,
  FormControl,
  Typography,
  Divider,
  Select,
  MenuItem,
  FormHelperText,
  Button,
  Snackbar,
  Alert,
} from "@mui/material";
import * as Yup from "yup";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import axios from "axios";
import { DragAndDrop } from "../../common/DragAndDrop";

export const CreateOOORequest: React.FC = () => {
  const { user } = useContext(UserContext);
  const [showSnackbar, setShowSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState("");
  const [alertStatus, setAlertStatus] = useState<AlertStatus>(AlertStatus.Info);
  const [loading, setLoading] = useState(false);
  const [supportingDocs, setSupportingDocs] = useState<File[]>([]);
  const navigate = useNavigate();

  if (!user) {
    return (
      <Typography variant="h4">Please log in to access this page</Typography>
    );
  }

  const requesterStaffId = user.id;

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  // Function to handle Snackbar close
  const handleCloseSnackBar = () => {
    setShowSnackbar(false);
  };

  // Handle form submission
  const handleSubmit = async (
    values: any,
    { resetForm }: { resetForm: () => void }
  ) => {
    setLoading(true);

    // Check if the start date is a weekend
    if (isWeekend(new Date(values.startDate))) {
      setAlertStatus(AlertStatus.Error);
      setSnackbarMessage("You cannot request OOO on a weekend.");
      setShowSnackbar(true);
      setLoading(false);
      return;
    }

    // Build the payload
    const payload = {
      requester_staff_id: requesterStaffId,
      ooo_date: values.startDate.toISOString().split("T")[0],
      reason_description: values.reason,
    };

    try {
      const form = new FormData();

      Object.keys(payload).forEach((key) => {
        form.append(key, (payload as any)[key]);
      });

      supportingDocs.forEach((file) => {
        form.append("supporting_docs", file);
      });

      await axios.post(`${BACKEND_URL}/arrangements/ooo-request`, form, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      setAlertStatus(AlertStatus.Success);
      setSnackbarMessage("Your OOO request was successfully submitted!");
      setShowSnackbar(true);

      // Clear the form after submission
      resetForm();
    } catch (error) {
      console.error("Error submitting the OOO request:", error);
      setAlertStatus(AlertStatus.Error);
      setSnackbarMessage("An error occurred while submitting your request.");
      setShowSnackbar(true);
    } finally {
      setLoading(false);
    }
  };

  // Yup form validation schema
  const validationSchema = Yup.object().shape({
    reason: Yup.string().required('Reason is required'),
    startDate: Yup.date().required('Start date is required').min(addDays(new Date(), 1), 'Start date must be at least 1 day from today'),
  });

  return (
    <Container maxWidth="sm">
      <Formik
        initialValues={{
          reason: "",
          startDate: new Date(),
          endDate: new Date(),
          supportingDocs: [],
        }}
        validationSchema={validationSchema}
        onSubmit={handleSubmit}
      >
        {({ values, setFieldValue }) => (
          <Form>
            <Typography variant="h4" sx={{ mb: 2 }}>
              OOO Request Form
            </Typography>
            <Divider sx={{ mb: 2 }} />

            {/* Reason */}
            <FormControl fullWidth sx={{ mb: 2 }}>
              <Typography variant="subtitle1">Reason for OOO</Typography>
              <Field
                name="reason"
                as="textarea"
                fullWidth
                required
                disabled={loading}
                className="border border-gray-300 rounded p-2 w-full"
              />
              <FormHelperText error>
                <ErrorMessage name="reason" />
              </FormHelperText>
            </FormControl>

            {/* Date Picker
            <FormControl fullWidth sx={{ mb: 2 }}>
              <Typography variant="subtitle1">OOO StartDate</Typography>
              <DatePicker
                selected={values.startDate}
                onChange={(date) => setFieldValue("startDate", date)}
                dateFormat="dd/MM/yyyy"
                customInput={<TextField fullWidth />}
                required
                minDate={addDays(new Date(), 1)}  // Disable today and only allow future dates
                disabled={loading}
              />
              <FormHelperText error>
                <ErrorMessage name="startDate" />
              </FormHelperText>
            </FormControl> */}

            {/* OOO Start Date Picker */}
{/* OOO Start Date Picker */}
<FormControl fullWidth sx={{ mb: 2 }}>
  <Typography variant="subtitle1">OOO Start Date</Typography>
  <DatePicker
    selected={values.startDate}
    onChange={(date) => {
      setFieldValue("startDate", date);
      // Reset end date if start date is set and end date is before start date
      if (date && values.endDate && date > values.endDate) {
        setFieldValue("endDate", null); // Reset end date if it's before the new start date
      }
    }}
    dateFormat="dd/MM/yyyy"
    customInput={<TextField fullWidth />}
    required
    minDate={addDays(new Date(), 1)} // Disable today and only allow future dates
    disabled={loading}
  />
  <FormHelperText error>
    <ErrorMessage name="startDate" />
  </FormHelperText>
</FormControl>

{/* OOO End Date Picker */}
<FormControl fullWidth sx={{ mb: 2 }}>
  <Typography variant="subtitle1">OOO End Date</Typography>
  <DatePicker
    selected={values.endDate} // Use values.endDate
    onChange={(date) => setFieldValue("endDate", date)}
    dateFormat="dd/MM/yyyy"
    customInput={<TextField fullWidth />}
    required
    minDate={values.startDate ? addDays(new Date(values.startDate), 1) : undefined} // Ensure end date is after start date
    disabled={loading || !values.startDate} // Disable if no start date is selected
  />
  <FormHelperText error>
    <ErrorMessage name="endDate" />
  </FormHelperText>
</FormControl>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <Typography variant="subtitle1">
                Upload Supporting Documents
              </Typography>
              <DragAndDrop
                maxFileSize={5 * 1000 * 1000}
                maxFiles={3}
                multiple={true}
                onFileAccepted={(files: File[]) => {
                  setSupportingDocs(files);
                }}
              />
            </FormControl>

            {/* Submit Button */}
            <Box sx={{ display: "flex", justifyContent: "flex-end", mt: 4 }}>
              <Button
                variant="outlined"
                color="primary"
                onClick={() => navigate(-1)}
                sx={{ mr: 2 }}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                color="primary"
                disabled={loading}
              >
                {loading ? "Submitting..." : "Submit"}
              </Button>
            </Box>
          </Form>
        )}
      </Formik>

      {/* Snackbar Component for Warning or Success */}
      <Snackbar
        open={showSnackbar}
        onClose={handleCloseSnackBar}
        anchorOrigin={{ vertical: "top", horizontal: "center" }}
        autoHideDuration={
          alertStatus === AlertStatus.Success &&
          snackbarMessage.includes("successfully submitted")
            ? null
            : 6000
        }
      >
        <Alert
          onClose={handleCloseSnackBar}
          severity={alertStatus}
          sx={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default CreateOOORequest;