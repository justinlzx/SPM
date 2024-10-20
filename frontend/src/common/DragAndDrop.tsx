import { useCallback, useEffect, useState } from "react";
import Dropzone from "react-dropzone";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import { Button, List, ListItem } from "@mui/material";
import AttachFileIcon from "@mui/icons-material/AttachFile";
import CloseIcon from "@mui/icons-material/Close";

type TDragAndDrop = {
  files: File[];
  maxFileSize: number;
  maxFiles: number;
  multiple?: boolean;
  onFileAccepted: (files: File[]) => void;
};

export const DragAndDrop = ({
  files: initialFiles,
  maxFileSize,
  maxFiles,
  multiple,
  onFileAccepted,
}: TDragAndDrop) => {
  const [files, setFiles] = useState<File[]>(initialFiles);

  useEffect(() => {
    setFiles(initialFiles);
  }, [initialFiles]);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      let updatedFiles;
      if (multiple) {
        updatedFiles = [...files, ...acceptedFiles];
      } else {
        updatedFiles = acceptedFiles;
      }
      setFiles(updatedFiles);
      onFileAccepted(updatedFiles); // Use updated files here
    },
    [onFileAccepted, files, multiple]
  );

  const onDeleteImage = (index: number) => {
    const newFiles = files.filter((_, i) => i !== index);
    setFiles(newFiles);
    onFileAccepted(newFiles);
  };

  const acceptedFiles = {
    "image/*": [".jpg", ".jpeg", ".png"],
    "application/pdf": [".pdf"],
  };

  return (
    <div>
      <Dropzone
        maxFiles={maxFiles}
        maxSize={maxFileSize}
        accept={acceptedFiles}
        multiple={multiple}
        onDrop={onDrop}
      >
        {({ fileRejections, getRootProps, getInputProps, isDragActive }) => (
          <div {...getRootProps()}>
            <input {...getInputProps()} />
            <div className={` ${isDragActive && "bg-black bg-opacity-5"}`}>
              <div className="rounded-sm items-center text-center p-4 border border-gray-200">
                <p className="text-[18px] mt-2">
                  Click or drag file to this area to upload file
                </p>
                <p className="mt-2 text-slate-500">5MB max file size</p>
                <CloudUploadIcon fontSize="medium" />
              </div>
              {fileRejections.length > 0 && (
                <div className="text-red-500 mt-2">
                  {fileRejections.map(({ file, errors }) => (
                    <div key={file.path}>
                      {errors.map((e) => (
                        <p key={e.code}>
                          {e.code === "file-too-large"
                            ? "File is larger than 5MB"
                            : e.message}
                        </p>
                      ))}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </Dropzone>
      <List>
        {files.map((file, idx) => (
          <ListItem
            key={file.name}
            className="flex justify-between hover:bg-gray-100"
          >
            <div className="flex items-center w-full">
              <AttachFileIcon />
              <span className="ml-2">{file.name}</span>
            </div>
            <Button className="justify-end" onClick={() => onDeleteImage(idx)}>
              <CloseIcon />
            </Button>
          </ListItem>
        ))}
      </List>
    </div>
  );
};
