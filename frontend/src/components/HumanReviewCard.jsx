import { Avatar, Box, Button, Card, Stack, TextField, Typography } from "@mui/material";
import { PsychologyRounded } from "@mui/icons-material";

function renderQuestion(question) {
  const normalized = question.replace(/\s+/g, " ").trim();
  const confirmMarker = "Please confirm:";
  const confirmIndex = normalized.indexOf(confirmMarker);

  if (confirmIndex === -1) {
    return normalized.split(/\n\s*\n/).map((paragraph, index) => (
      <Typography
        key={`question-${index}`}
        component="p"
        sx={{
          m: 0,
          mt: index ? 1.25 : 0,
          color: "#30394d",
          fontSize: 16,
          fontWeight: 650,
          lineHeight: 1.65,
          whiteSpace: "pre-line",
        }}
      >
        {paragraph.trim()}
      </Typography>
    ));
  }

  const context = normalized.slice(0, confirmIndex).trim();
  const request = normalized.slice(confirmIndex + confirmMarker.length).trim();
  const reasonMarker = "I cannot draft";
  const reasonIndex = request.indexOf(reasonMarker);
  const confirmations = (reasonIndex === -1 ? request : request.slice(0, reasonIndex))
    .split(/\(\d+\)\s*/)
    .map((item) => item.trim())
    .filter(Boolean);
  const reason = reasonIndex === -1 ? "" : request.slice(reasonIndex).trim();

  return (
    <Stack spacing={1.5}>
      <Box>
        <Typography variant="overline" sx={sectionLabelSx}>
          Request context
        </Typography>
        <Typography sx={questionTextSx}>{context}</Typography>
      </Box>
      <Box sx={sectionBoxSx}>
        <Typography variant="overline" sx={sectionLabelSx}>
          Confirmation needed
        </Typography>
        <Box component="ol" sx={{ m: 0, pl: 2.5 }}>
          {confirmations.map((item, index) => (
            <Box component="li" key={`confirmation-${index}`} sx={{ pl: 0.5 }}>
              <Typography sx={questionTextSx}>{item}</Typography>
            </Box>
          ))}
        </Box>
      </Box>
      {reason && (
        <Box>
          <Typography variant="overline" sx={sectionLabelSx}>
            Why your input is needed
          </Typography>
          <Typography sx={questionTextSx}>{reason}</Typography>
        </Box>
      )}
    </Stack>
  );
}

const sectionLabelSx = {
  color: "#7b6a4b",
  fontSize: 11,
  fontWeight: 800,
  letterSpacing: ".08em",
};

const questionTextSx = {
  color: "#30394d",
  fontSize: 15.5,
  fontWeight: 600,
  lineHeight: 1.65,
};

const sectionBoxSx = {
  p: { xs: 1.5, md: 2 },
  bgcolor: "rgba(255, 255, 255, .72)",
  border: "1px solid rgba(180, 145, 79, .2)",
  borderRadius: 2,
};

export function HumanReviewCard({
  request,
  answer,
  onAnswerChange,
  onSubmit,
  saving,
  readOnly = false,
}) {
  return (
    <Card
      sx={{ p: { xs: 2, md: 3 }, bgcolor: "#fffaf3", borderColor: "#f2d29b" }}
    >
      <Stack direction="row" spacing={1.5} alignItems="flex-start">
        <Avatar sx={{ bgcolor: "#fff4dc", color: "#9b6b1f" }}>
          <PsychologyRounded />
        </Avatar>
        <Box flex={1}>
          <Typography
            variant="overline"
            color="#7b6a4b"
            fontWeight={800}
            letterSpacing=".08em"
          >
            Human review required
          </Typography>
          <Box sx={{ mt: 0.75, mb: 1.5 }}>
            {renderQuestion(request.question)}
          </Box>
          {readOnly ? (
            <Box sx={{ mt: 2, p: 2, bgcolor: "white", borderRadius: 2 }}>
              <Typography variant="overline" color="text.secondary" fontWeight={800}>
                Approved answer
              </Typography>
              <Typography mt={0.5}>{request.answer || "No answer recorded"}</Typography>
              <Typography variant="caption" color="text.secondary" display="block" mt={1}>
                Approved {request.answered_at ? new Date(request.answered_at).toLocaleString() : "—"}
              </Typography>
            </Box>
          ) : (
            <>
              <TextField
                fullWidth
                multiline
                minRows={3}
                value={answer}
                onChange={(event) => onAnswerChange(event.target.value)}
                placeholder="Add your decision or clarification..."
                sx={{
                  mt: 2,
                  bgcolor: "white",
                  "& .MuiInputBase-input": {
                    fontSize: 15,
                    lineHeight: 1.6,
                  },
                }}
              />
              <Button
                variant="contained"
                color="secondary"
                onClick={onSubmit}
                disabled={!answer.trim() || saving}
                sx={{ mt: 1.5 }}
              >
                Save human answer
              </Button>
            </>
          )}
        </Box>
      </Stack>
    </Card>
  );
}
