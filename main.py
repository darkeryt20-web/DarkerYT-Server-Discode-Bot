const { Client, GatewayIntentBits, ActivityType, EmbedBuilder, ApplicationCommandOptionType, ChannelType } = require('discord.js');
const { joinVoiceChannel } = require('@discordjs/voice');
const { initializeApp } = require('firebase/app');
const { getFirestore, doc, setDoc, getDoc } = require('firebase/firestore');

const firebaseConfig = {
  apiKey: "AIzaSyAEI93SAWsTPULIONvwp2UhI_5wBkfUTDo",
  authDomain: "studio-9486178597-80f56.firebaseapp.com",
  projectId: "studio-9486178597-80f56",
  storageBucket: "studio-9486178597-80f56.firebasestorage.app",
  messagingSenderId: "532281979014",
  appId: "1:532281979014:web:41b8a030f75970111ca107"
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildVoiceStates,
    GatewayIntentBits.GuildMessages
  ]
});

const TOKEN = "M_TOKEN";
let statusIntervals = new Map();

client.once('ready', async () => {
  console.log(`${client.user.tag} is online.`);

  const commands = [
    {
      name: 'setchannel',
      description: 'Set the voice channel for the bot to join on startup',
      options: [{ name: 'channel', type: ApplicationCommandOptionType.Channel, description: 'Select a voice channel', required: true }]
    },
    {
      name: 'setstatus',
      description: 'Set or update a custom streaming status',
      options: [
        { name: 'id', type: ApplicationCommandOptionType.Integer, description: 'Status ID/Position', required: true },
        { name: 'text', type: ApplicationCommandOptionType.String, description: 'Status text', required: true }
      ]
    },
    {
      name: 'removestatus',
      description: 'Remove a status by ID',
      options: [{ name: 'id', type: ApplicationCommandOptionType.Integer, description: 'Status ID to remove', required: true }]
    },
    {
      name: 'getstatus',
      description: 'Get list of all saved statuses'
    },
    {
      name: 'setbotchannel',
      description: 'Set current channel for startup notifications'
    }
  ];

  await client.application.commands.set(commands);

  client.guilds.cache.forEach(async (guild) => {
    const docRef = doc(db, "guilds", guild.id);
    const docSnap = await getDoc(docRef);

    if (docSnap.exists()) {
      const data = docSnap.data();

      if (data.voiceChannelId) {
        try {
          joinVoiceChannel({
            channelId: data.voiceChannelId,
            guildId: guild.id,
            adapterCreator: guild.voiceAdapterCreator,
          });
        } catch (e) {}
      }

      if (data.textChannelId) {
        const channel = guild.channels.cache.get(data.textChannelId);
        if (channel) {
          const fetchedUser = await client.users.fetch(client.user.id, { force: true });
          const embed = new EmbedBuilder()
            .setTitle("Bot Online")
            .setDescription("Gida text ekak dapu ekak")
            .setThumbnail(client.user.displayAvatarURL({ dynamic: true }))
            .setColor("#5865F2");
          
          if (fetchedUser.bannerURL()) {
            embed.setImage(fetchedUser.bannerURL({ size: 1024 }));
          }

          channel.send({ embeds: [embed] }).catch(() => {});
        }
      }

      if (data.statuses && data.statuses.length > 0) {
        startStatusRotation(guild.id, data.statuses);
      }
    }
  });
});

function startStatusRotation(guildId, statuses) {
  if (statusIntervals.has(guildId)) {
    clearInterval(statusIntervals.get(guildId));
  }

  let index = 0;
  const updateActivity = () => {
    if (!statuses || statuses.length === 0) {
      client.user.setPresence({ activities: [] });
      return;
    }
    const current = statuses[index];
    client.user.setActivity(current.text, {
      type: ActivityType.Streaming,
      url: 'https://www.twitch.tv/discord'
    });
    index = (index + 1) % statuses.length;
  };

  updateActivity();
  const interval = setInterval(updateActivity, 10000); 
  statusIntervals.set(guildId, interval);
}

client.on('interactionCreate', async (interaction) => {
  if (!interaction.isChatInputCommand()) return;

  if (interaction.guild.ownerId !== interaction.user.id) {
    return interaction.reply({ content: "Meka use karanna puluvan Server Owner ta vitharai.", ephemeral: true });
  }

  const { commandName, options, guildId, channelId } = interaction;
  const docRef = doc(db, "guilds", guildId);
  const docSnap = await getDoc(docRef);
  let data = docSnap.exists() ? docSnap.data() : { statuses: [] };

  if (commandName === 'setchannel') {
    const channel = options.getChannel('channel');
    if (channel.type !== ChannelType.GuildVoice) {
      return interaction.reply({ content: "Karunakarala Voice Channel ekak thoranna.", ephemeral: true });
    }

    data.voiceChannelId = channel.id;
    await setDoc(docRef, data, { merge: true });

    joinVoiceChannel({
      channelId: channel.id,
      guildId: guildId,
      adapterCreator: interaction.guild.voiceAdapterCreator,
    });

    return interaction.reply({ content: `Voice channel eka set kala: ${channel.name}`, ephemeral: true });
  }

  if (commandName === 'setstatus') {
    const id = options.getInteger('id');
    const text = options.getString('text');

    let statuses = data.statuses || [];
    const existingIndex = statuses.findIndex(s => s.id === id);

    if (existingIndex !== -1) {
      statuses[existingIndex].text = text;
    } else {
      statuses.push({ id, text });
    }

    statuses.sort((a, b) => a.id - b.id);
    data.statuses = statuses;

    await setDoc(docRef, data, { merge: true });
    startStatusRotation(guildId, statuses);

    return interaction.reply({ content: `Status eka ID ${id} lata update kala.`, ephemeral: true });
  }

  if (commandName === 'removestatus') {
    const id = options.getInteger('id');
    let statuses = data.statuses || [];

    const filtered = statuses.filter(s => s.id !== id);
    const updatedStatuses = filtered.map((s, idx) => ({
      id: idx + 1,
      text: s.text
    }));

    data.statuses = updatedStatuses;
    await setDoc(docRef, data, { merge: true });
    startStatusRotation(guildId, updatedStatuses);

    return interaction.reply({ content: `ID ${id} status eka ain kala saha okkoma re-index kala.`, ephemeral: true });
  }

  if (commandName === 'getstatus') {
    let statuses = data.statuses || [];
    if (statuses.length === 0) {
      return interaction.reply({ content: "Kisima status ekak saved ne.", ephemeral: true });
    }

    const embed = new EmbedBuilder()
      .setTitle("Saved Statuses")
      .setColor("#5865F2");

    let description = "";
    statuses.forEach(s => {
      description += `**ID:** ${s.id} | **Text:** ${s.text}\n`;
    });

    embed.setDescription(description);
    return interaction.reply({ embeds: [embed], ephemeral: true });
  }

  if (commandName === 'setbotchannel') {
    data.textChannelId = channelId;
    await setDoc(docRef, data, { merge: true });
    return interaction.reply({ content: "Bot online notification channel eka set kala.", ephemeral: true });
  }
});

client.login(TOKEN);
