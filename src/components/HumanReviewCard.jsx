import { Avatar, Box, Button, Card, Stack, TextField, Typography } from "@mui/material";
import { PsychologyRounded } from "@mui/icons-material";

export function HumanReviewCard({ request, answer, onAnswerChange, onSubmit, saving }) {
  return (
    <Card
      sx={{ p: { xs: 2, md: 3 }, bgcolor: "#fffaf3", borderColor: "#f2d29b" }}
    >
      <Stack direction="row" spacing={1.5} alignItems="flex-start">
        <Avatar sx={{ bgcolor: "#fff0cf", color: "#b97900" }}>
          <PsychologyRounded />
        </Avatar>
        <Box flex={1}>
          <Typography variant="overline" color="#a36a00" fontWeight={800}>
            Human review required
          </Typography>
          <Typography variant="h5" mt={0.3}>
            {request.question}
          </Typography>
          <TextField
            fullWidth
            multiline
            minRows={3}
            value={answer}
            onChange={(event) => onAnswerChange(event.target.value)}
            placeholder="Add your decision or clarification..."
            sx={{ mt: 2, bgcolor: "white" }}
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
        </Box>
      </Stack>
    </Card>
  );
}
