CREATE TABLE IF NOT EXISTS guilds (
        GuildID integer PRIMARY KEY,
        Prefix text DEFAULT "!"
);

CREATE TABLE IF NOT EXISTS feedback_channel (
        GuildID integer PRIMARY KEY,
        ChannelID integer
);
