import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  Box,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Checkbox,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { transactionsAPI, categoriesAPI } from '../services/api';
import { format } from 'date-fns';

function Transactions() {
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [selected, setSelected] = useState([]);

  // Filters
  const [filters, setFilters] = useState({
    search: '',
    category_id: '',
    transaction_type: '',
    start_date: null,
    end_date: null,
  });

  // Edit dialog
  const [editDialog, setEditDialog] = useState({
    open: false,
    transaction: null,
    category_id: '',
    createRule: false,
  });

  useEffect(() => {
    loadCategories();
  }, []);

  useEffect(() => {
    loadTransactions();
  }, [page, rowsPerPage, filters]);

  const loadCategories = async () => {
    try {
      const response = await categoriesAPI.list();
      setCategories(response.data);
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  };

  const loadTransactions = async () => {
    setLoading(true);
    try {
      const params = {
        page: page + 1,
        limit: rowsPerPage,
        ...filters,
        start_date: filters.start_date ? format(filters.start_date, 'yyyy-MM-dd') : undefined,
        end_date: filters.end_date ? format(filters.end_date, 'yyyy-MM-dd') : undefined,
      };

      // Remove empty filters
      Object.keys(params).forEach(key => {
        if (params[key] === '' || params[key] === null || params[key] === undefined) {
          delete params[key];
        }
      });

      const response = await transactionsAPI.list(params);
      setTransactions(response.data);
    } catch (error) {
      console.error('Error loading transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters({
      ...filters,
      [field]: value,
    });
    setPage(0);
  };

  const handleSelectTransaction = (id) => {
    const selectedIndex = selected.indexOf(id);
    let newSelected = [];

    if (selectedIndex === -1) {
      newSelected = newSelected.concat(selected, id);
    } else if (selectedIndex === 0) {
      newSelected = newSelected.concat(selected.slice(1));
    } else if (selectedIndex === selected.length - 1) {
      newSelected = newSelected.concat(selected.slice(0, -1));
    } else if (selectedIndex > 0) {
      newSelected = newSelected.concat(
        selected.slice(0, selectedIndex),
        selected.slice(selectedIndex + 1),
      );
    }

    setSelected(newSelected);
  };

  const handleEditTransaction = (transaction) => {
    setEditDialog({
      open: true,
      transaction,
      category_id: transaction.category_id || '',
      createRule: false,
    });
  };

  const handleSaveEdit = async () => {
    try {
      await transactionsAPI.update(
        editDialog.transaction.id,
        { category_id: editDialog.category_id },
        editDialog.createRule
      );
      setEditDialog({ open: false, transaction: null, category_id: '', createRule: false });
      loadTransactions();
    } catch (error) {
      console.error('Error updating transaction:', error);
    }
  };

  const handleBulkUpdate = async (categoryId) => {
    try {
      await transactionsAPI.bulkUpdate(selected, categoryId);
      setSelected([]);
      loadTransactions();
    } catch (error) {
      console.error('Error bulk updating:', error);
    }
  };

  const getTypeChipColor = (type) => {
    switch (type) {
      case 'charge':
        return 'error';
      case 'payment':
        return 'success';
      case 'refund':
        return 'info';
      default:
        return 'default';
    }
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Transactions
        </Typography>

        {/* Filters */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Search"
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                placeholder="Merchant or description"
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={filters.category_id}
                  onChange={(e) => handleFilterChange('category_id', e.target.value)}
                >
                  <MenuItem value="">All</MenuItem>
                  {categories.map((cat) => (
                    <MenuItem key={cat.id} value={cat.id}>
                      {cat.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Type</InputLabel>
                <Select
                  value={filters.transaction_type}
                  onChange={(e) => handleFilterChange('transaction_type', e.target.value)}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="charge">Charge</MenuItem>
                  <MenuItem value="payment">Payment</MenuItem>
                  <MenuItem value="refund">Refund</MenuItem>
                  <MenuItem value="fee">Fee</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <DatePicker
                label="Start Date"
                value={filters.start_date}
                onChange={(date) => handleFilterChange('start_date', date)}
                slotProps={{ textField: { fullWidth: true } }}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <DatePicker
                label="End Date"
                value={filters.end_date}
                onChange={(date) => handleFilterChange('end_date', date)}
                slotProps={{ textField: { fullWidth: true } }}
              />
            </Grid>
            <Grid item xs={12} md={1}>
              <Button
                fullWidth
                variant="outlined"
                onClick={() => setFilters({ search: '', category_id: '', transaction_type: '', start_date: null, end_date: null })}
                sx={{ height: '56px' }}
              >
                Clear
              </Button>
            </Grid>
          </Grid>
        </Paper>

        {/* Bulk Actions */}
        {selected.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body1" sx={{ mb: 1 }}>
              {selected.length} selected
            </Typography>
            <FormControl sx={{ minWidth: 200, mr: 2 }}>
              <InputLabel>Set Category</InputLabel>
              <Select
                defaultValue=""
                onChange={(e) => handleBulkUpdate(e.target.value)}
              >
                {categories.map((cat) => (
                  <MenuItem key={cat.id} value={cat.id}>
                    {cat.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        )}

        {/* Transactions Table */}
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox">
                  <Checkbox
                    indeterminate={selected.length > 0 && selected.length < transactions.length}
                    checked={transactions.length > 0 && selected.length === transactions.length}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelected(transactions.map(t => t.id));
                      } else {
                        setSelected([]);
                      }
                    }}
                  />
                </TableCell>
                <TableCell>Date</TableCell>
                <TableCell>Merchant</TableCell>
                <TableCell>Description</TableCell>
                <TableCell>Category</TableCell>
                <TableCell>Amount</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {transactions.map((txn) => (
                <TableRow key={txn.id}>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selected.indexOf(txn.id) !== -1}
                      onChange={() => handleSelectTransaction(txn.id)}
                    />
                  </TableCell>
                  <TableCell>{format(new Date(txn.transaction_date), 'MMM dd, yyyy')}</TableCell>
                  <TableCell>{txn.merchant_name}</TableCell>
                  <TableCell>{txn.description}</TableCell>
                  <TableCell>
                    <Chip
                      label={txn.category_name || 'Uncategorized'}
                      size="small"
                      color={txn.category_name === 'Uncategorized' ? 'default' : 'primary'}
                    />
                  </TableCell>
                  <TableCell>${parseFloat(txn.amount).toFixed(2)}</TableCell>
                  <TableCell>
                    <Chip label={txn.transaction_type} size="small" color={getTypeChipColor(txn.transaction_type)} />
                  </TableCell>
                  <TableCell>
                    <Button size="small" onClick={() => handleEditTransaction(txn)}>
                      Edit
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <TablePagination
            component="div"
            count={-1}
            page={page}
            onPageChange={(e, newPage) => setPage(newPage)}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={(e) => {
              setRowsPerPage(parseInt(e.target.value, 10));
              setPage(0);
            }}
            rowsPerPageOptions={[25, 50, 100]}
          />
        </TableContainer>

        {/* Edit Dialog */}
        <Dialog open={editDialog.open} onClose={() => setEditDialog({ ...editDialog, open: false })}>
          <DialogTitle>Edit Transaction</DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 2 }}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={editDialog.category_id}
                  onChange={(e) => setEditDialog({ ...editDialog, category_id: e.target.value })}
                >
                  <MenuItem value="">Uncategorized</MenuItem>
                  {categories.map((cat) => (
                    <MenuItem key={cat.id} value={cat.id}>
                      {cat.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Box sx={{ mt: 2 }}>
                <label>
                  <Checkbox
                    checked={editDialog.createRule}
                    onChange={(e) => setEditDialog({ ...editDialog, createRule: e.target.checked })}
                  />
                  Create rule for this merchant
                </label>
              </Box>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setEditDialog({ ...editDialog, open: false })}>Cancel</Button>
            <Button onClick={handleSaveEdit} variant="contained">Save</Button>
          </DialogActions>
        </Dialog>
      </Container>
    </LocalizationProvider>
  );
}

export default Transactions;
