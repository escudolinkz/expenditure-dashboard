import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  LinearProgress,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { statementsAPI } from '../services/api';
import { format } from 'date-fns';

function Statements() {
  const [statements, setStatements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploadDialog, setUploadDialog] = useState(false);
  const [uploadData, setUploadData] = useState({
    file: null,
    card_name: '',
    card_last4: '',
    bank_type: 'generic',
  });
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadStatements();
  }, []);

  const loadStatements = async () => {
    setLoading(true);
    try {
      const response = await statementsAPI.list();
      setStatements(response.data);
    } catch (error) {
      console.error('Error loading statements:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
      setUploadData({ ...uploadData, file });
    } else {
      alert('Please select a PDF file');
    }
  };

  const handleUpload = async () => {
    if (!uploadData.file) {
      alert('Please select a file');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadData.file);
      formData.append('card_name', uploadData.card_name);
      formData.append('card_last4', uploadData.card_last4);
      formData.append('bank_type', uploadData.bank_type);
      formData.append('auto_parse', 'true');

      await statementsAPI.upload(formData);

      setUploadDialog(false);
      setUploadData({
        file: null,
        card_name: '',
        card_last4: '',
        bank_type: 'generic',
      });

      // Reload statements after a delay to allow background parsing
      setTimeout(() => {
        loadStatements();
      }, 2000);
    } catch (error) {
      console.error('Error uploading statement:', error);
      alert('Upload failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this statement?')) {
      return;
    }

    try {
      await statementsAPI.delete(id);
      loadStatements();
    } catch (error) {
      console.error('Error deleting statement:', error);
    }
  };

  const handleReparse = async (id) => {
    try {
      await statementsAPI.parse(id);
      loadStatements();
    } catch (error) {
      console.error('Error reparsing statement:', error);
    }
  };

  const handleRecategorize = async (id) => {
    try {
      await statementsAPI.recategorize(id);
      alert('Recategorization completed');
    } catch (error) {
      console.error('Error recategorizing:', error);
    }
  };

  const getStatusChipColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'processing':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Statements
        </Typography>
        <Button
          variant="contained"
          startIcon={<UploadIcon />}
          onClick={() => setUploadDialog(true)}
        >
          Upload Statement
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>File Name</TableCell>
              <TableCell>Card</TableCell>
              <TableCell>Period</TableCell>
              <TableCell>Bank Type</TableCell>
              <TableCell>Transactions</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Uploaded</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {statements.map((statement) => (
              <TableRow key={statement.id}>
                <TableCell>{statement.filename}</TableCell>
                <TableCell>
                  {statement.card_name || 'Unknown'}
                  {statement.card_last4 && ` ****${statement.card_last4}`}
                </TableCell>
                <TableCell>
                  {statement.period_start && statement.period_end
                    ? `${format(new Date(statement.period_start), 'MMM dd, yyyy')} - ${format(new Date(statement.period_end), 'MMM dd, yyyy')}`
                    : 'N/A'}
                </TableCell>
                <TableCell>{statement.bank_type}</TableCell>
                <TableCell>{statement.transaction_count || 0}</TableCell>
                <TableCell>
                  <Chip
                    label={statement.parse_status}
                    size="small"
                    color={getStatusChipColor(statement.parse_status)}
                  />
                  {statement.parse_error && (
                    <Typography variant="caption" color="error" display="block">
                      {statement.parse_error}
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  {format(new Date(statement.uploaded_at), 'MMM dd, yyyy HH:mm')}
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => handleReparse(statement.id)}
                    title="Re-parse"
                  >
                    <RefreshIcon />
                  </IconButton>
                  <Button
                    size="small"
                    onClick={() => handleRecategorize(statement.id)}
                  >
                    Recategorize
                  </Button>
                  <IconButton
                    size="small"
                    onClick={() => handleDelete(statement.id)}
                    color="error"
                    title="Delete"
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
            {statements.length === 0 && !loading && (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Typography variant="body1" color="text.secondary" sx={{ py: 4 }}>
                    No statements uploaded yet. Click "Upload Statement" to get started.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Upload Dialog */}
      <Dialog open={uploadDialog} onClose={() => setUploadDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Upload Statement</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Button
              variant="outlined"
              component="label"
              fullWidth
              sx={{ mb: 2 }}
            >
              {uploadData.file ? uploadData.file.name : 'Select PDF File'}
              <input
                type="file"
                hidden
                accept=".pdf"
                onChange={handleFileSelect}
              />
            </Button>

            <TextField
              fullWidth
              label="Card Name (Optional)"
              value={uploadData.card_name}
              onChange={(e) => setUploadData({ ...uploadData, card_name: e.target.value })}
              sx={{ mb: 2 }}
              placeholder="e.g., Chase Sapphire"
            />

            <TextField
              fullWidth
              label="Card Last 4 Digits (Optional)"
              value={uploadData.card_last4}
              onChange={(e) => setUploadData({ ...uploadData, card_last4: e.target.value.slice(0, 4) })}
              sx={{ mb: 2 }}
              placeholder="1234"
              inputProps={{ maxLength: 4 }}
            />

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Bank Type</InputLabel>
              <Select
                value={uploadData.bank_type}
                onChange={(e) => setUploadData({ ...uploadData, bank_type: e.target.value })}
              >
                <MenuItem value="generic">Generic (Auto-detect)</MenuItem>
                <MenuItem value="chase">Chase</MenuItem>
                <MenuItem value="amex">American Express</MenuItem>
                <MenuItem value="citi">Citibank</MenuItem>
                <MenuItem value="bofa">Bank of America</MenuItem>
              </Select>
            </FormControl>

            {uploading && <LinearProgress />}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialog(false)} disabled={uploading}>
            Cancel
          </Button>
          <Button onClick={handleUpload} variant="contained" disabled={!uploadData.file || uploading}>
            {uploading ? 'Uploading...' : 'Upload'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default Statements;
