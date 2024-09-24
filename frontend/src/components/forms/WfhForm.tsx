import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Formik, Form, Field, ErrorMessage } from 'formik';
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
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from '@mui/material';
import ErrorIcon from '@mui/icons-material/Error';
import { Recurring } from './Recurring';
import * as Yup from 'yup';
import DatePicker from 'react-datepicker';
import axios from 'axios';
import dayjs from 'dayjs';

interface WfhFormProps {
  reason: string;
  startDate: Date;
  endDate: Date | null;
  wfhType: 'full' | 'am' | 'pm' | '';
  repeatInterval: number;
  repeatIntervalUnit: 'week' | 'month';
  occurrences: number;
}

export const WfhForm = () => {
  const [scheduleType, setScheduleType] = useState<'adhoc' | 'recurring'>('adhoc');
  const [wfhDaysTaken] = useState(3); // Hardcoded number of WFH days taken
  const [isSnackbarOpen, setIsSnackbarOpen] = useState(false); // Control Snackbar visibility
  const [isDialogOpen, setIsDialogOpen] = useState(false); // Control dialog visibility
  const [proceedWithSubmission, setProceedWithSubmission] = useState(false); // Control whether to proceed with form submission
  const [isSuccessDialogOpen, setIsSuccessDialogOpen] = useState(false); // Control success dialog visibility
  const navigate = useNavigate();

  // Helper function to check if WFH days exceed the limit
  const checkExceedLimit = (
    startDate: Date,
    occurrences: number,
    repeatIntervalUnit: string,
    repeatInterval: number,
    wfhDaysTaken: number
  ) => {
    let wfhCount = wfhDaysTaken;
    const start = dayjs(startDate);
    const currentMonth = start.month();

    if (scheduleType === 'adhoc') {
      wfhCount += 1;
    } else {
      let countOccInMonth = 0;
      for (let i = 0; i < occurrences; i++) {
        const nextDate = start.add(i * repeatInterval, repeatIntervalUnit as 'week' | 'month');
        if (nextDate.month() === currentMonth) {
          countOccInMonth += 1;
        }
      }
      wfhCount += countOccInMonth;
    }

    return wfhCount > 2;
  };

  // Handle form submission
  const handleSubmit = async (values: WfhFormProps) => {
    const exceeded = checkExceedLimit(
      values.startDate,
      values.occurrences,
      values.repeatIntervalUnit,
      values.repeatInterval,
      wfhDaysTaken
    );

    if (exceeded && !proceedWithSubmission) {
      setIsSnackbarOpen(true); // Show warning Snackbar
      setIsDialogOpen(true); // Open confirmation dialog
      return;
    }

    // Prepare payload
    const payload = {
      requester_staff_id: 12345,
      wfh_date: values.startDate.toISOString().split('T')[0],
      wfh_type: values.wfhType.toLowerCase(),
      reason_description: values.reason,
      endDate: scheduleType === 'recurring' ? values.endDate?.toISOString().split('T')[0] : null,
    };

    try {
      const response = await axios.post('https://your-api-endpoint.com/arrangement', payload);
      console.log(response.data);
      setIsSuccessDialogOpen(true); // Open success dialog
    } catch (error) {
      console.error(error);
    }
  };

  // Yup form validation
  const validationSchema = Yup.object().shape({
    reason: Yup.string().required('Reason is required'),
    startDate: Yup.date().required('Start date is required'),
    wfhType: Yup.string().required('You must select AM, PM, or Full-day'),
    endDate: Yup.date().nullable().when(() => {
      return scheduleType === 'recurring'
        ? Yup.date().required('End date is required for recurring schedules')
        : Yup.date().nullable();
    }),
    repeatInterval: Yup.number().when(() => {
      return scheduleType === 'recurring'
        ? Yup.number().required('Repeat interval is required')
        : Yup.number().nullable();
    }),
    occurrences: Yup.number().when(() => {
      return scheduleType === 'recurring'
        ? Yup.number().required('Occurrences are required')
        : Yup.number().nullable();
    }),
    repeatIntervalUnit: Yup.string().when(() => {
      return scheduleType === 'recurring'
        ? Yup.string().required('Repeat interval unit is required')
        : Yup.string().nullable();
    }),
  });

  return (
    <Container maxWidth="sm">
      <Formik
        initialValues={{
          reason: '',
          startDate: new Date(),
          endDate: null,
          wfhType: '',
          repeatInterval: 1,
          repeatIntervalUnit: 'week',
          occurrences: 1,
        }}
        validationSchema={validationSchema}
        onSubmit={handleSubmit}
      >
        {({ values, setFieldValue }) => (
          <Form>
            {/* Reason for WFH */}
            <Typography variant="h4" sx={{ mb:2}}>
              WFH Request Form
            </Typography>
            <Divider sx={{mb:2}}/>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <Typography variant="subtitle1">Reason for WFH</Typography>
              <Field name="reason" as={TextField} fullWidth required />
              <FormHelperText error>
                <ErrorMessage name="reason" />
              </FormHelperText>
            </FormControl>

            {/* AM, PM, Full-day Select */}
            <FormControl fullWidth sx={{ mb: 2 }}>
              <Typography variant="subtitle1">WFH Type</Typography>
              <Select
                name="wfhType"
                value={values.wfhType}
                onChange={(e) => setFieldValue('wfhType', e.target.value)}
                fullWidth
              >
                <MenuItem value="" disabled>
                  Select WFH Type
                </MenuItem>
                <MenuItem value="full">Full-day</MenuItem>
                <MenuItem value="am">AM</MenuItem>
                <MenuItem value="pm">PM</MenuItem>
              </Select>
              <FormHelperText error>
                <ErrorMessage name="wfhType" />
              </FormHelperText>
            </FormControl>

            {/* Schedule Type: Adhoc or Recurring */}
            <FormControl fullWidth sx={{ mb: 2 }}>
              <Typography variant="subtitle1">Schedule Type</Typography>
              <Select
                name="scheduleType"
                value={scheduleType}
                onChange={(e) => setScheduleType(e.target.value as 'adhoc' | 'recurring')}
                fullWidth
              >
                <MenuItem value="adhoc">Ad-hoc</MenuItem>
                <MenuItem value="recurring">Recurring</MenuItem>
              </Select>
              <FormHelperText error>
                <ErrorMessage name="scheduleType" />
              </FormHelperText>
            </FormControl>

            {/* Date */}
            {scheduleType === 'adhoc' && (
              <FormControl fullWidth sx={{ mb: 2 }}>
                <Typography variant="subtitle1">WFH Date</Typography>
                <DatePicker
                  selected={values.startDate}
                  onChange={(date) => setFieldValue('startDate', date)}
                  dateFormat="dd/MM/yyyy"
                  customInput={<TextField fullWidth />}
                  required
                  minDate={new Date()} // Disable dates before today
                />
                <FormHelperText error>
                  <ErrorMessage name="startDate" />
                </FormHelperText>
              </FormControl>
            )}

            {/* Conditionally render recurring fields */}
            {scheduleType === 'recurring' && (
              <Recurring values={values} setFieldValue={setFieldValue} />
            )}

            {/* Submit and Cancel Buttons */}
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 4 }}>
              <Button
                type="button"
                sx={{ backgroundColor: 'gray', color: 'white', mr: 2 }}
                onClick={() => navigate('/home')}
              >
                Cancel
              </Button>

              <Button type="submit" variant="contained" color="primary">
                Submit
              </Button>
            </Box>
          </Form>
        )}
      </Formik>

      {/* Snackbar Warning */}
      {/* <Snackbar
        open={isSnackbarOpen}
        autoHideDuration={6000}
        onClose={() => setIsSnackbarOpen(false)}
      >
        <Alert onClose={() => setIsSnackbarOpen(false)} severity="warning">
          You have exceeded the allowed 2 WFH days per month. Do you want to proceed?
        </Alert>
      </Snackbar> */}

      {/* Dialog for user confirmation */}
      <Dialog open={isDialogOpen} onClose={() => setIsDialogOpen(false)}>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <ErrorIcon color="warning" sx={{ fontSize: 24, marginRight: 1 }} />
            Warning
          </Box>
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            You are about to exceed 2 WFH days for this month. Are you sure you would like to
            proceed with this request?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIsDialogOpen(false)} color="primary">
            Cancel
          </Button>
          <Button
            onClick={() => {
              setIsDialogOpen(false);
              setProceedWithSubmission(true); // Allow form submission on confirmation
            }}
            color="primary"
            autoFocus
          >
            Proceed
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success Dialog for successful submission */}
      <Dialog open={isSuccessDialogOpen} onClose={() => setIsSuccessDialogOpen(false)}>
        <DialogTitle>Success</DialogTitle>
        <DialogContent>
          <DialogContentText>Your request was successfully submitted.</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => navigate('/home')} color="primary">
            Back to Home
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default WfhForm;
