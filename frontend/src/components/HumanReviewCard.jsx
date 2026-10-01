import { Avatar, Box, Button, Card, Stack, TextField, Typography } from "@mui/material";
import { PsychologyRounded } from "@mui/icons-material";

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
            {request.question.split(/\n\s*\n/).map((paragraph, index) => (
              <Typography
                key={`${request.id}-question-${index}`}
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
            ))}
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
