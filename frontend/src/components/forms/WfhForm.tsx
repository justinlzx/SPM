import React, { useState } from 'react';
import { Formik, Form, Field, ErrorMessage } from 'formik';
import { Box, Container, TextField, FormControl, Typography, Select, MenuItem, FormHelperText, Button } from '@mui/material';
import * as Yup from 'yup';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import axios from 'axios';
import { Recurring } from './Recurring'; // Import Recurring component

// Define form values interface
interface WfhFormProps {
  reason: string;
  startDate: Date;
  endDate: Date | null; // Nullable for adhoc schedules
  wfhType: 'full' | 'am' | 'pm' | '';
  repeatInterval: number;
  repeatIntervalUnit: 'week' | 'month';
  occurrences: number;
}

export const WfhForm = () => {
  const [scheduleType, setScheduleType] = useState<'adhoc' | 'recurring'>('adhoc'); 

  const handleSubmit = async (values: WfhFormProps) => {
    const payload = {
      //TO REPLACE ID
      requester_staff_id: 12345, 
      wfh_date: values.startDate.toISOString().split('T')[0], 
      wfh_type: values.wfhType.toLowerCase(),
      reason_description: values.reason,
      //endDate: scheduleType === 'recurring' ? values.endDate?.toISOString().split('T')[0] : null, // Only include endDate for recurring
    };

    try {
      const response = await axios.post('https://your-api-endpoint.com/arrangement', payload);
      console.log(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  const validationSchema = Yup.object().shape({
    reason: Yup.string().required('Reason is required'),
    startDate: Yup.date().required('Start date is required'),
    wfhType: Yup.string().required('You must select AM, PM, or Full-day'),

    // Conditionally require endDate based on the schedule type
    endDate: Yup.date().nullable().when(() => {
      return scheduleType === 'recurring'
        ? Yup.date().required('End date is required for recurring schedules')
        : Yup.date().nullable();
    }),

    // Conditionally validate repeatInterval and occurrences only if schedule is recurring
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
    <Container maxWidth="sm" sx={{ mt: 4 }}>
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
                <MenuItem value="" disabled>Select WFH Type</MenuItem>
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
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 4, position: 'relative' }}>
              <Button
                type="button"
                sx={{ backgroundColor: 'gray', color: 'white', mr: 2 }}
                onClick={() => console.log("Form canceled")}
              >
                Cancel
              </Button>

              <Button
                type="submit"
                sx={{
                  backgroundColor: 'blue',
                  color: 'white',
                  '&:hover': { backgroundColor: 'darkblue' },
                }}
              >
                Submit
              </Button>
            </Box>
          </Form>
        )}
      </Formik>
    </Container>
  );
};

export default WfhForm;
