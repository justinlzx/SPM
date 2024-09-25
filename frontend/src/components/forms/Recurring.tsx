import React, { useEffect } from 'react';
import { FormControl, Typography, TextField, FormHelperText, Select, MenuItem } from '@mui/material';
import { ErrorMessage, useFormikContext } from 'formik';
import DatePicker from 'react-datepicker';

export const Recurring: React.FC = () => {
  const { values, errors, touched, setFieldValue } = useFormikContext<any>();

  useEffect(() => {
    if (values.startDate && values.occurrences > 0 && values.repeatInterval > 0) {
      let calculatedEndDate = new Date(values.startDate);
      
      // Calculate based on repeatIntervalUnit
      if (values.repeatIntervalUnit === 'week') {
        calculatedEndDate.setDate(calculatedEndDate.getDate() + values.occurrences * values.repeatInterval * 7);
      } else if (values.repeatIntervalUnit === 'month') {
        calculatedEndDate.setMonth(calculatedEndDate.getMonth() + values.occurrences * values.repeatInterval);
      }

      // Set calculated end date
      setFieldValue('endDate', calculatedEndDate);
    }
  }, [values.startDate, values.occurrences, values.repeatInterval, values.repeatIntervalUnit, setFieldValue]);

  return (
    <>
      {/* Start Date */}
      <div style={{ display: 'flex', gap: '16px' }}>
        <FormControl fullWidth sx={{ mb: 2 }}>
          <Typography variant="subtitle1">Start Date</Typography>
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

        {/* End Date (read-only) */}
        <FormControl fullWidth sx={{ mb: 2 }}>
          <Typography variant="subtitle1">End Date</Typography>
          <TextField
            value={values.endDate ? new Intl.DateTimeFormat('en-GB').format(values.endDate) : ''}
            fullWidth
            disabled
          />
          <FormHelperText>
            End date is automatically calculated based on the recurrence pattern.
          </FormHelperText>
        </FormControl>
      </div>

      {/* Repeat Interval */}
      <FormControl fullWidth sx={{ mb: 2 }}>
        <Typography variant="subtitle1">Repeats Every</Typography>
        <div style={{ display: 'flex', gap: '16px' }}>
          <TextField
            name="repeatInterval"
            type="number"
            value={values.repeatInterval}
            onChange={(e) => setFieldValue('repeatInterval', e.target.value)}
            inputProps={{ min: 1 }}
            fullWidth
            sx={{ flex: 1 }}
          />
          <Select
            name="repeatIntervalUnit"
            value={values.repeatIntervalUnit}
            onChange={(e) => setFieldValue('repeatIntervalUnit', e.target.value)}
            sx={{ flex: 1 }}
          >
            <MenuItem value="week">week(s)</MenuItem>
            <MenuItem value="month">month(s)</MenuItem>
          </Select>
        </div>
        {errors.repeatInterval && touched.repeatInterval && (
          <FormHelperText error>
            <ErrorMessage name="repeatInterval" />
          </FormHelperText>
        )}
      </FormControl>

      {/* Occurrences */}
      <FormControl fullWidth sx={{ mb: 2 }}>
        <Typography variant="subtitle1">Number of Occurrences</Typography>
        <TextField
          name="occurrences"
          type="number"
          value={values.occurrences}
          onChange={(e) => setFieldValue('occurrences', e.target.value)}
          inputProps={{ min: 1 }}
          fullWidth
        />
        {errors.occurrences && touched.occurrences && (
          <FormHelperText error>
            <ErrorMessage name="occurrences" />
          </FormHelperText>
        )}
      </FormControl>
    </>
  );
};

export default Recurring;
