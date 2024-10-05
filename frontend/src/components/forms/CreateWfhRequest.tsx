import React, { useContext, useState } from 'react';
import { UserContext } from '../../context/UserContextProvider';
import { useNavigate } from 'react-router-dom';
import { Formik, Form, Field, ErrorMessage } from 'formik';
import { addWeeks, addMonths, isAfter, isWeekend } from 'date-fns';
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
} from '@mui/material';
import * as Yup from 'yup';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import axios from 'axios';
import qs from 'qs';
import { Recurring } from './Recurring';

export const CreateWfhRequest: React.FC = () => {
  const { user } = useContext(UserContext);
  const [scheduleType, setScheduleType] = useState<'adhoc' | 'recurring'>('adhoc');
  const [wfhDaysTaken] = useState(1); 
  const [showSnackbar, setShowSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [alertStatus, setAlertStatus] = useState<AlertStatus>(AlertStatus.Info); 
  const [loading, setLoading] = useState(false);
  const [proceedWithSubmission, setProceedWithSubmission] = useState(false); 
  const navigate = useNavigate();

  if (!user) {
    return <Typography variant="h4">Please log in to access this page</Typography>;
  }

  const requesterStaffId = user.id;

  // Function to handle Snackbar close
  const handleCloseSnackBar = () => {
    setShowSnackbar(false);
  };

  // Function to generate recurring dates
  const generateRecurringDates = (start: Date, end: Date, interval: number, unit: string) => {
    let current = new Date(start);
    const recurringDates: Date[] = [];
    const weekendDates: Date[] = [];

    while (isAfter(end, current) || current.getTime() === end.getTime()) {
      if (!isWeekend(current)) {
        recurringDates.push(new Date(current));
      } else {
        weekendDates.push(new Date(current));
      }

      // Increment date based on the repeat interval and unit
      if (unit === 'week') {
        current = addWeeks(current, interval);
      } else if (unit === 'month') {
        current = addMonths(current, interval);
      }
    }

    return { recurringDates, weekendDates };
  };

  // Handle form submission
  const handleSubmit = async (values: any, { resetForm }: { resetForm: () => void }) => {
    setLoading(true);
    let recurringDates: Date[] = [];
    const start = new Date(values.startDate);
    const end = new Date(values.endDate);

    // Check if WFH limit has been exceeded
    if (wfhDaysTaken >= 2 && !proceedWithSubmission) {
      setAlertStatus(AlertStatus.Warning);
      setSnackbarMessage('You have already used 2 WFH days this month. Are you sure you want to proceed?');
      setShowSnackbar(true);
      setProceedWithSubmission(true);
      setLoading(false);
      return;
    }

    // Check if the start date is a weekend
    if (scheduleType === 'adhoc' && isWeekend(start)) {
      setAlertStatus(AlertStatus.Error);
      setSnackbarMessage('You cannot request WFH on a weekend.');
      setShowSnackbar(true);
      setLoading(false);
      return;
    }

    // Check for weekend dates in recurring and year limit
    if (scheduleType === 'recurring') {
      const oneYearLater = new Date(start);
      oneYearLater.setFullYear(start.getFullYear() + 1);

      if (end > oneYearLater) {
        setAlertStatus(AlertStatus.Error);
        setSnackbarMessage('End date is more than 1 year from start date.');
        setShowSnackbar(true);
        setLoading(false);
        return;
      }

      // Generate recurring dates based on repeat interval and unit
      const { recurringDates: validRecurringDates, weekendDates: removedWeekends } = generateRecurringDates(
        start,
        end,
        values.repeatInterval,
        values.repeatIntervalUnit
      );

      recurringDates = validRecurringDates;

      // Warn if weekends are removed
      if (removedWeekends.length > 0) {
        setAlertStatus(AlertStatus.Warning);
        setSnackbarMessage(
          `Some dates fall on a weekend and have been removed: ${removedWeekends
            .map((date) => date.toISOString().split('T')[0])
            .join(', ')}`
        );
        setShowSnackbar(true);
      }

      // Prevent submission if no valid dates remain
      if (recurringDates.length === 0) {
        setAlertStatus(AlertStatus.Error);
        setSnackbarMessage('No valid dates after removing weekends. Please adjust your schedule.');
        setShowSnackbar(true);
        setLoading(false);
        return;
      }
    }

    // Build the payload
    const payload = {
      requester_staff_id: requesterStaffId,
      wfh_date: values.startDate.toISOString().split('T')[0],
      wfh_type: values.wfhType.toLowerCase(),
      reason_description: values.reason,
      is_recurring: scheduleType === 'recurring',
      ...(scheduleType === 'recurring' && {
        recurring_end_date: values.endDate ? values.endDate.toISOString().split('T')[0] : null,
        recurring_frequency_number: values.repeatInterval,
        recurring_frequency_unit: values.repeatIntervalUnit,
        recurring_occurrences: values.occurrences,
      }),
    };

    try {
      await axios.post('http://localhost:8000/arrangement/request', qs.stringify(payload), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      setAlertStatus(AlertStatus.Success);
      setSnackbarMessage('Your request was successfully submitted!');
      setShowSnackbar(true);

      // Clear the form after submission
      resetForm();
    } catch (error) {
      console.error('Error submitting the WFH arrangement:', error);
      setAlertStatus(AlertStatus.Error);
      setSnackbarMessage('An error occurred while submitting your request.');
      setShowSnackbar(true);
    } finally {
      setLoading(false);
    }
  };

  // Yup form validation schema
  const validationSchema = Yup.object().shape({
    reason: Yup.string().required('Reason is required'),
    startDate: Yup.date().required('Start date is required'),
    wfhType: Yup.string().required('You must select AM, PM, or Full-day'),
    endDate: Yup.date()
      .nullable()
      .test('is-recurring-end-date', 'End date is required for recurring schedules', function (value) {
        const { scheduleType } = this.parent;
        return scheduleType === 'recurring' ? !!value : true;
      })
      .test('is-within-1-year', 'End date must be within 1 year from start date', function (value) {
        const { scheduleType, startDate } = this.parent;
        if (scheduleType === 'recurring' && value) {
          const oneYearLater = new Date(startDate);
          oneYearLater.setFullYear(startDate.getFullYear() + 1);
          return value <= oneYearLater;
        }
        return true;
      }),
    repeatInterval: Yup.number()
      .nullable()
      .test('is-recurring-repeat-interval', 'Repeat interval is required for recurring schedules', function (value) {
        const { scheduleType } = this.parent;
        return scheduleType === 'recurring' ? !!value : true;
      }),
    occurrences: Yup.number()
      .nullable()
      .test('is-recurring-occurrences', 'Occurrences are required for recurring schedules', function (value) {
        const { scheduleType } = this.parent;
        return scheduleType === 'recurring' ? !!value : true;
      }),
    repeatIntervalUnit: Yup.string()
      .nullable()
      .test('is-recurring-repeat-interval-unit', 'Repeat interval unit is required for recurring schedules', function (value) {
        const { scheduleType } = this.parent;
        return scheduleType === 'recurring' ? !!value : true;
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
        {({ values, setFieldValue, resetForm }) => (
          <Form>
            <Typography variant="h4" sx={{ mb: 2 }}>
              WFH Request Form
            </Typography>
            <Divider sx={{ mb: 2 }} />

            {/* Reason */}
            <FormControl fullWidth sx={{ mb: 2 }}>
              <Typography variant="subtitle1">Reason for WFH</Typography>
              <Field name="reason" as={TextField} fullWidth required />
              <FormHelperText error>
                <ErrorMessage name="reason" />
              </FormHelperText>
            </FormControl>

            {/* WFH Type */}
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

            {/* Schedule Type */}
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
            </FormControl>

            {/* Date Picker */}
            {scheduleType === 'adhoc' && (
              <FormControl fullWidth sx={{ mb: 2 }}>
                <Typography variant="subtitle1">WFH Date</Typography>
                <DatePicker
                  selected={values.startDate}
                  onChange={(date) => setFieldValue('startDate', date)}
                  dateFormat="dd/MM/yyyy"
                  customInput={<TextField fullWidth />}
                  required
                  minDate={new Date()}
                />
                <FormHelperText error>
                  <ErrorMessage name="startDate" />
                </FormHelperText>
              </FormControl>
            )}

            {/* Recurring Fields */}
            {scheduleType === 'recurring' && <Recurring />}

            {/* Submit Button */}
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 4 }}>
              <Button variant="outlined" color="primary" onClick={() => navigate(-1)} sx={{ mr: 2 }}>
                Cancel
              </Button>
              <Button type="submit" variant="contained" color="primary" disabled={loading}>
                {loading ? 'Submitting...' : 'Submit'}
              </Button>
            </Box>
          </Form>
        )}
      </Formik>

      {/* Snackbar Component for Warning or Success */}
      <Snackbar
          open={showSnackbar}
          onClose={handleCloseSnackBar}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
          autoHideDuration={alertStatus === AlertStatus.Success && snackbarMessage.includes('successfully submitted') ? null : 6000}
        >
          <Alert
            onClose={handleCloseSnackBar}
            severity={alertStatus}
            sx={{ 
              width: '100%',
              display: 'flex', // Use flexbox for alignment
              alignItems: 'center', // Center items vertically
              justifyContent: 'space-between', // Spread content evenly
            }}
            action={
              alertStatus === AlertStatus.Success && snackbarMessage.includes('successfully submitted') && (
                <Button
                  color="inherit"
                  size="small"
                  variant="contained"
                  onClick={() => navigate('/home')}
                  sx={{
                    backgroundColor: '#006400', // Dark green fill color
                    color: '#FFFFFF', // White text
                    textTransform: 'none', // Keep text case as-is
                    lineHeight: '1.5', // Adjust line height for better alignment
                    whiteSpace: 'nowrap', // Prevent the text from wrapping to a new line
                    '&:hover': {
                      backgroundColor: '#004d00', // Slightly darker shade for hover effect
                    },
                    marginLeft: 'auto', // Align button to the right
                  }}
                >
                  Back to Home
                </Button>
              )
            }
          >
            {snackbarMessage}
          </Alert>
        </Snackbar>
    </Container>
  );
};

export default CreateWfhRequest;