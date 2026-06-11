import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import AntibioticRiskOverview from './components/AntibioticRiskOverview';
import CrossPathogenComparison from './components/CrossPathogenComparison';
import GeneDrivers from './components/GeneDrivers';
import MapVisualization from './components/MapVisualization';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import { analyzeSample, uploadFasta, getAntibiotics } from './services/api';
import { Upload, FileText, Activity } from 'lucide-react';

// Antibiotics list is now fetched dynamically from the API in the component.

// Default demo isolate profile (e.g. MDR Klebsiella)
const DEFAULT_GENE_PRESENCE = {
  "blaNDM": 1,      // Carbapenemase
  "blaCTX_M": 1,    // ESBL
  "gyrA_D87N": 1,   // Ciprofloxacin resistance
  "qnrS": 1,        // Plasmid-mediated quinolone resistance
  "aac6Ib_cr": 1,   // Aminoglycoside mod gene
  "armA": 1         // High-level amikacin resistance
};

function App() {
  const [antibiotics, setAntibiotics] = useState([]);
  const [selectedAntibiotic, setSelectedAntibiotic] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentGenes, setCurrentGenes] = useState(DEFAULT_GENE_PRESENCE);
  const [fileName, setFileName] = useState("Demo Isolate A");
  const [uploadStatus, setUploadStatus] = useState("");

  useEffect(() => {
    const loadAntibiotics = async () => {
      try {
        const list = await getAntibiotics();
        if (list && list.length > 0) {
          const formattedList = list.map(ab => ({
            id: ab.toLowerCase(),
            name: ab,
            class: 'N/A' // Class logic resides in backend
          }));
          setAntibiotics(formattedList);
          setSelectedAntibiotic(formattedList[0].id);
        }
      } catch (err) {
        console.error("Failed to load antibiotics", err);
      }
    };
    loadAntibiotics();
  }, []);

  useEffect(() => {
    if (selectedAntibiotic) {
      fetchAnalysis();
    }
  }, [selectedAntibiotic, currentGenes]);

  const fetchAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await analyzeSample(selectedAntibiotic, currentGenes);
      // Transform API response to fit UI components
      const transformedData = {
        overallRisk: response.overall_risk_score,
        riskLevel: response.risk_category,
        confidence: 0.95, // Model stability metric
        pathogens: response.pathogen_breakdown.map(p => ({
          name: p.name,
          risk: p.risk,
          count: p.risk_mass ? Object.keys(p.risk_mass).length : 0 // Fallback if count not explicitly provided
        })),
        genes: Object.entries(response.gene_drivers).map(([name, detail]) => ({
          name: name,
          score: detail.score,
          direction: detail.direction === 'Resistant' ? 'increase' : 'decrease'
        })),
        aggregation: [
          { step: 'Pathogen Models', description: 'Individual pathogen readings' },
          { step: 'Gene Contributions', description: 'Weighted genetic markers' },
          { step: 'GAARA Aggregation', description: 'Cross-pathogen synthesis' },
          { step: 'Antibiotic Risk', description: 'Final predictive score' }
        ]
      };
      setData(transformedData);
    } catch (err) {
      console.error(err);
      setError("Failed to fetch analysis from server. Ensure backend is running.");
    }
    setLoading(false);
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadStatus("Uploading...");
    try {
      const res = await uploadFasta(file);
      setFileName(file.name);
      if (res.status === 'validation_phase') {
        setUploadStatus("Uploaded (Validation Phase - No Genes Extracted)");
      } else if (res.status === 'success') {
        setUploadStatus(`Analysis Complete. Found ${Object.keys(res.genes).length} genes.`);
        if (res.genes && Object.keys(res.genes).length > 0) {
          setCurrentGenes(res.genes);
        }
      }
    } catch (err) {
      setUploadStatus("Upload Failed");
    }
  };

  return (
    <div className="app">
      <Header />
      <main className="container">
        {/* Sample Input Section */}
        <section className="card flex-row" style={{ justifyContent: 'space-between', alignItems: 'center', padding: 'var(--spacing-md)' }}>
          <div className="flex-row" style={{ gap: '12px' }}>
            <div style={{ backgroundColor: 'var(--color-background)', padding: '8px', borderRadius: '50%' }}>
              <FileText size={20} color="var(--color-primary)" />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1rem' }}>Current Sample: {fileName}</h3>
              <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                {uploadStatus || "Using default demo gene profile"}
              </p>
            </div>
          </div>

          <div>
            <label htmlFor="fasta-upload" style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              backgroundColor: 'var(--color-primary)',
              color: 'white',
              padding: '8px 16px',
              borderRadius: 'var(--radius-sm)',
              cursor: 'pointer',
              fontWeight: 500,
              fontSize: '0.9rem'
            }}>
              <Upload size={16} />
              Upload FASTA
            </label>
            <input
              id="fasta-upload"
              type="file"
              accept=".fasta,.fa"
              onChange={handleFileUpload}
              style={{ display: 'none' }}
            />
          </div>
        </section>

        {loading && !data ? (
          <div style={{ textAlign: 'center', padding: '2rem' }}>Processing GAARA Model...</div>
        ) : error ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-danger)' }}>{error}</div>
        ) : data ? (
          <>
            {/* Section 1 */}
            <AntibioticRiskOverview
              selectedAntibiotic={selectedAntibiotic}
              onAntibioticChange={setSelectedAntibiotic}
              antibioticList={antibiotics}
              data={data}
            />

            <div className="grid-2">
              {/* Section 2 */}
              <CrossPathogenComparison data={data} />

              {/* Section 3 */}
              <GeneDrivers data={data} />
            </div>

            {/* Section 4 removed as per request */}

            {/* Section 5: Maps */}
            <MapVisualization />

            {/* Section 6: Analytics */}
            <AnalyticsDashboard />
          </>
        ) : null}
      </main>
    </div>
  );
}

export default App;
