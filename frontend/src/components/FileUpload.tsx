import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileImage } from 'lucide-react';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  loading?: boolean;
  accept?: Record<string, string[]>;
}

export function FileUpload({
  onFileSelect,
  loading = false,
  accept = { 'image/*': ['.png', '.jpg', '.jpeg', '.webp'], 'application/pdf': ['.pdf'] },
}: FileUploadProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFileSelect(acceptedFiles[0]);
      }
    },
    [onFileSelect],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxFiles: 1,
    disabled: loading,
  });

  return (
    <div
      {...getRootProps()}
      className={`card cursor-pointer border-2 border-dashed transition-all duration-200 ${
        isDragActive
          ? 'border-brand-400 bg-brand-900/20'
          : 'border-game-border hover:border-brand-500/50'
      } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center justify-center py-12 text-center">
        {loading ? (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-400 mb-4" />
            <p className="text-gray-300">Processing rulebook...</p>
            <p className="text-sm text-gray-500 mt-1">OCR extraction & rule structuring in progress</p>
          </>
        ) : (
          <>
            {isDragActive ? (
              <FileImage className="h-12 w-12 text-brand-400 mb-4" />
            ) : (
              <Upload className="h-12 w-12 text-gray-400 mb-4" />
            )}
            <p className="text-gray-300 font-medium">
              {isDragActive ? 'Drop your rulebook here' : 'Drag & drop a rulebook image or PDF'}
            </p>
            <p className="text-sm text-gray-500 mt-1">or click to browse (PNG, JPG, PDF up to 20MB)</p>
          </>
        )}
      </div>
    </div>
  );
}
